import pika
import threading
import time
import requests
import json
import os
import amqpstorm

#INICIALIZAÇÕES:
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
nome_exchange = 'promocoes'
exchange = channel.exchange_declare('promocoes', exchange_type='direct')
global filas_declaradas
filas_declaradas = []
global tags
tags = []
global channels
channels = []

#Duas funções mágicas para listar todas as filas disponíveis
'''def call_rabbitmq_api(host, port, user='guest', passwd='guest'):
  url = 'http://%s:%s/api/queues' % (host, port)
  r = requests.get(url, auth=(user,passwd))
  return r

def get_queue_name(json_list):
  res = []
  for json in json_list:
    res.append(json["name"])
  return res'''


def consumidor(nome_fila: str):
    global tags
    global channels
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channels.append(channel)
    tag = channel.basic_consume(queue=nome_fila, on_message_callback=callback, auto_ack=True)
    tags.append(tag)
    channel.start_consuming()



def callback(ch, method, properties, body):
    print(f" [x] {method.routing_key}:{body}")


def main():
    #global ouvindo_filas
    global filas_declaradas
    global tags
    global channels
    threads = []
    while (True):
        entrada = '\n'
        while entrada == '\n' or entrada == '?' or entrada == '' or entrada == '--ouvindo':
            entrada = input("Quais filas serão ouvidas (separe por vírgula): ")
            #res = call_rabbitmq_api('localhost', 15672)
            #q_name = get_queue_name(res.json())
            #if entrada == '?':
           #     print("Filas disponíveis: ", end='')
           #     print(q_name)

        entrada_dividida = entrada.split(sep=',')


        for canal in channels:
            for item in tags:
                canal.basic_cancel(item)
        
        filas_declaradas = []
        threads = []
        tags = []
        channels = []

        i = 0
        for item in entrada_dividida:
            fila_tmp = channel.queue_declare(queue='')
            nome_fila = fila_tmp.method.queue
            filas_declaradas.append(nome_fila)
            channel.queue_bind(nome_fila, nome_exchange, item)
            thr = threading.Thread(target=consumidor, args=(nome_fila,))
            thr.start()
            threads.append(thr)
            i += 1



if __name__ == '__main__':
    main()
