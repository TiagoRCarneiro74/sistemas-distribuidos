import binascii

import pika
import threading
import time
import requests
import json
import os
import random
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

#INICIALIZAÇÕES:
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
nome_exchange = 'principal'
exchange = channel.exchange_declare(nome_exchange, exchange_type='direct')

#Duas funções mágicas para listar todas as filas disponíveis
def call_rabbitmq_api(host, port, user='guest', passwd='guest'):
  url = 'http://%s:%s/api/queues' % (host, port)
  r = requests.get(url, auth=(user,passwd))
  return r

def get_queue_name(json_list):
  res = []
  for json in json_list:
    res.append(json["name"])
  return res

arq_cpr = open("id_rsa", 'rb')
cpr = arq_cpr.read()
chave_privada = RSA.import_key(cpr)
arq_cpb = open("id_rsa.pub", 'rb')
cpb = arq_cpb.read()
chave_publica = RSA.import_key(cpb)
assinador = pkcs1_15.new(chave_privada)

def callback_reserva(ch, method, properties, body):
    msg = body

    texto_msg = msg.decode("raw_unicode_escape")
    print(texto_msg.encode("raw_unicode_escape"))
    print("Nova reserva criada: {}".format(texto_msg))

    hash = SHA256.new(texto_msg.encode("raw_unicode_escape"))
    #hash_tratado = hash.digest()
    #print(hash_tratado)
    assinatura = assinador.sign(hash)

    verificador = pkcs1_15.PKCS115_SigScheme(chave_publica)
    try:

        verificador.verify(hash, assinatura)
    except:
        print("Assinatura Inválida")
    #print("ASSINATURA: " + (assinatura.decode("raw_unicode_escape")))
    nova_msg = (texto_msg + ";").encode("raw_unicode_escape") + assinatura
    #print("AQUI É A NOVA MSG")
    #print(nova_msg)
    if random.random() > 0.5:
        channel.basic_publish(exchange=nome_exchange, routing_key='pagamento-aprovado', body=nova_msg)
        print("Pagamento Aprovado")
    else:
        channel.basic_publish(exchange=nome_exchange, routing_key='pagamento-recusado', body=nova_msg)
        print("Pagamento Recusado")


def ouvir_fila(routing_key, callback):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    fila = channel.queue_declare(queue='')
    nome_fila = fila.method.queue
    channel.queue_bind(nome_fila, 'principal', routing_key=routing_key)
    tag = channel.basic_consume(queue=nome_fila, on_message_callback=callback, auto_ack=True)
    # tags.append(tag)
    channel.start_consuming()



def main():
    thread_ouvir = threading.Thread(target=ouvir_fila, args=('reserva-criada', callback_reserva))
    thread_ouvir.start()


if __name__ == '__main__':
    main()
