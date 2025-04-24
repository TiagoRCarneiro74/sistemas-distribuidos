import pika
import os
import random
import time
import math
import datetime
import threading
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

#INICIALIZAÇÕES:
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='reserva-criada')
nome_exchange = "MSReserva" + str(os.getpid())
exchange = channel.exchange_declare(nome_exchange, exchange_type='direct')

arq_cpb = open("id_rsa.pub", 'rb')
cpb = arq_cpb.read()
chave_publica = RSA.import_key(cpb)
verificador = pkcs1_15.PKCS115_SigScheme(chave_publica)

cidades = ["Shanghai","Singapura","Ningbo-Zhoushan","Shenzhen","Guangzhou","Busan","Hong Kong","Rotterdam","Antuerpia","Hamburgo","Los Angeles","Nova York","Dubai","Tanger Med", "Port Klang","Santos","Paranagua","Rio de Janeiro", "Itajai","Salvador","Suape","Rio Grande","Vitoria","Manaus","Sao Luis"]
navios = ["Estrela do Sul", "Horizonte Azul", "Vento Leste","Doomba","Wrestler","Hostile","Lobelia","Queen","Ruby","Cavendish","Barcross","Medusa","Wye","Argonaut","Etchingham","Braid","Dittany","Lenox","Confounder","Goderich","Deale","Anemone", "Sable"]

def str_time_prop(start, time_format, prop):
    stime = time.mktime(time.strptime(start, time_format))
    etime = time.mktime(time.strptime(str(time.strptime(start, time_format)[2])+"/"+str(time.strptime(start, time_format)[1]+1)+"/"+str(time.strptime(start, time_format)[0]), time_format))

    ptime = stime + prop * (etime - stime)

    return time.strftime(time_format, time.localtime(ptime))


def random_date(start, prop):
    return str_time_prop(start, '%d/%m/%Y', prop)

def callback_bilhete(ch, method, properties, body):
    print(f"Bilhete da reserva gerado com Sucesso: {body}")

def verificar_assinatura(msg):
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
        return 0
    else:
        print("Assinatura válida")
        return 1



def callback_pag_recusado(ch, method, properties, body):
    msg = body.decode("raw_unicode_escape")
    verificar_assinatura(msg)
    print("O pagamento da reserva foi recusado")


def callback_pag_aprovado(ch, method, properties, body):
    msg = body.decode("raw_unicode_escape")
    verificar_assinatura(msg)
    print("O pagamento da reserva foi aprovado - esperando bilhete...")


def ouvir_fila(routing_key, callback):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    fila = channel.queue_declare(queue='')
    nome_fila = fila.method.queue
    channel.queue_bind(nome_fila, 'principal', routing_key=routing_key)
    tag = channel.basic_consume(queue=nome_fila, on_message_callback=callback, auto_ack=True)
    # tags.append(tag)
    channel.start_consuming()

# Função geradora de itinerários
def itinerario(destino, data, porto):
    dados=[]
    for x in range(3):
        lugaresVisitados = math.floor(random.random()*15)
        noites = math.floor(random.random()*60)+5
        valor = math.floor(random.random()*15000)+1000
        retorno = random_date(data,  random.random())
        navio = random.choice(navios)
        dados.append("[" + str(
            x + 1) + "] Navio: " + navio + "\nEmbarque: " + porto + "\nDestino: " + destino + "\nData de Embarque: " + retorno + "\nNúmero de Paradas: " + str(
            lugaresVisitados) + "\nNúmero de noites: " + str(noites) + "\nValor por pessoa: " + str(valor))

        print(dados[x])
    
    while True:
        entrada = input("Selecione a viagem que queira reservar, caso não deseje essas reservas, digite 4: ").strip()
        if entrada =='1' or entrada =='2' or entrada =='3':
            fazer_reserva(dados[int(entrada)-1])
            break
        elif entrada =='4':
            break


def fazer_reserva(body):
    while True:
        cabines = input("Quantidade de cabines: ").strip()
        pessoas = input("Quantidade de pessoas: ").strip()
        if cabines.isnumeric() and pessoas.isnumeric():
            break
    channel.basic_publish(
        exchange='principal',
        routing_key='reserva-criada',
        body=body
    )
    print("www.pagamento.com/"+body)


def main():
    thread_bilhetes = threading.Thread(target=ouvir_fila, args=('bilhete-gerado', callback_bilhete))
    thread_bilhetes.daemon = True
    thread_bilhetes.start()

    thread_pag_apr = threading.Thread(target=ouvir_fila, args=('pagamento-aprovado', callback_pag_aprovado))
    thread_pag_apr.daemon = True
    thread_pag_apr.start()

    thread_pag_rec = threading.Thread(target=ouvir_fila, args=('pagamento-recusado', callback_pag_recusado))
    thread_pag_rec.daemon = True
    thread_pag_rec.start()

    continuar = 's'
    while continuar != 'n':
        entrada = '\n'
        while entrada != '1':
            entrada = input("O que gostaria de fazer?\n [1] Consultar\n").strip()

        aux = 1
        for cidade in cidades:
            print("["+str(aux)+"] "+cidade)
            aux+=1
        entrada=None
        while True:
            entrada = input("Qual cidade seria seu destino?").strip()
            if entrada.isnumeric() and int(entrada)<=len(cidades):
                break
            aux = 1
            for cidade in cidades:
                print("["+str(aux)+"] "+cidade)
                aux+=1
        destino = cidades[int(entrada)-1]
        aux = 1
        for cidade in cidades:
            print("["+str(aux)+"] "+cidade)
            aux+=1
        entrada=None
        while True:
            entrada = input("Qual seria o porto de embarque?").strip()
            if entrada.isnumeric() and int(entrada)<=len(cidades):
                break
            aux = 1
            for cidade in cidades:
                print("["+str(aux)+"] "+cidade)
                aux+=1
        porto = cidades[int(entrada)-1]
        while True:
            entrada = input("Qual é a data de embarque? (Ex. 20/02/2026)").strip()
            try:
                res = bool(datetime.datetime.strptime(entrada, "%d/%m/%Y"))
            except ValueError:
                res=False
            if res:
                break
        print("Chegou no itinerario")
        itinerario(destino, entrada, porto)
        time.sleep(3)
        #print("Passou do itinarario")
        continuar = input("Deseja fazer outra reserva? (s/n): ")

if __name__ == '__main__':
    main()
