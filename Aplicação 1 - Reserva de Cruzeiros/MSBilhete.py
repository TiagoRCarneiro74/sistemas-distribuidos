import pika
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
exchange = channel.exchange_declare('principal', exchange_type='direct')

arq_cpb = open("id_rsa.pub", 'rb')
cpb = arq_cpb.read()
chave_publica = RSA.import_key(cpb)
verificador = pkcs1_15.PKCS115_SigScheme(chave_publica)

def callback(ch, method, properties, body):
    print(f" [x] {method.routing_key}:{body}")

    #Verificar assinatura do pagamento:
    msg = body.decode("raw_unicode_escape")

    assinatura = msg[int(msg.find(";")) + 1:].encode("raw_unicode_escape")
    texto = msg[:int(msg.find(";"))]
    print(texto)
    hash = SHA256.new(texto.encode('raw_unicode_escape'))
    hash_tratado = hash.digest()
    print("ASSINATURA: {}".format(assinatura))
    print("HASH: {}".format(hash_tratado))
    print(texto.encode("raw_unicode_escape"))
    print(msg[int(msg.find(";")) + 1:])

    try:
        verificador.verify(hash, assinatura)
    except:
        print("Assinatura Inválida")

    print("Verificou a assinatura.")

    channel.basic_publish(exchange='principal', routing_key='bilhete-gerado', body=texto)

pag_apr = channel.queue_declare(queue='')
nome_fila = pag_apr.method.queue
channel.queue_bind(queue=nome_fila, exchange='principal', routing_key='pagamento-aprovado')
tag = channel.basic_consume(queue=nome_fila, on_message_callback=callback, auto_ack=True)
channel.start_consuming()