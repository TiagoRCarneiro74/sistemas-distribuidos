import pika
import requests
import json

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
exchange = channel.exchange_declare('promocoes', exchange_type='direct')

while (True):
    pre_filas = input("Publicar em quais destinos (separe por vírgula): ")
    filas = pre_filas.split(sep=',')


    msg = input("O que será publicado: ")

    for fila in filas:
        try:
            if fila is None:
               continue
            channel.basic_publish(exchange='promocoes',  # Inserir mensagem na fila
                                  routing_key=fila,
                                  body=msg)
        except:
            print("Erro ao publicar a mensagem na fila {}.".format(fila))
