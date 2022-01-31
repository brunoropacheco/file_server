# -*- coding: cp1252 -*-
# Echo server program
import socket, os
import sqlite3
from threading import Thread
from multiprocessing import Process
from time import sleep

def compare_onlyclient(usuario,nome_pasta,):
        num_files = int(conn.recv(1024))
        print num_files
        for i in range(num_files):
                comp_file = conn.recv(1024)#recebe nome de arquivo para checar
                print comp_file
                for name_dead in cursor.execute("SELECT * FROM \
dead_files_"+usuario+" WHERE element = ?", (comp_file,)):
                        exists = 1
                try:
                        if exists:
                                conn.send('1')
                                sleep(1)
                except:   
                        conn.send('0')
                        sleep(1)
                        nnf = conn.recv(1024)
                        lmnf = conn.recv(1024)
                        lnf = conn.recv(1024)
                        lnf = int(lnf)
                        cursor.execute("INSERT INTO last_mod_elemento_"+usuario+" \
                        (elemento,last_mod) VALUES (?,?)", (nnf,lmnf,))
                        data_bank.commit()
                        recebe=open(nome_pasta+'/'+nnf,'wb')
                        if lnf:
                                l = conn.recv(lnf)
                                recebe.write(l)
                                recebe.close()

def compare_onlyserver(usuario,nome_pasta,):
        num_files = int(conn.recv(1024))
        print num_files
        for files in range(num_files):
                name_file = conn.recv(1024)
                print name_file
                aredead = int(conn.recv(1024))
                print aredead
                if aredead:
                        os.remove(nomepasta+'/'+name_file)
                        death_time = str(time())
                        cursor.execute("INSERT INTO dead_files_"+usuario+" (element,death_time) VALUES (?,?)", (name_file,death_time,))
                        cursor.execute("DELETE FROM last_mod_elemento"+usuario+" WHERE elemento = ?", (name_file,))            
                else:
                    #Algoritmo de envio de arquivo por socket foi tirado de http://stackoverflow.com/questions/9382045/send-a-file-through-sockets-in-python
                    open_file = open(nome_pasta+'/'+name_file, "rb")
                    lenght = os.stat(nome_pasta+'/'+name_file)[6]
                    print lenght
                    conn.send(str(lenght))
                    sleep(1)
                    if lenght:
                            l = open_file.read(lenght)
                            conn.send(l)
                            sleep(1)
                            open_file.close()
                

def pasta_modificada(nome_pasta,usuario,):
        cursor.execute('CREATE TABLE IF NOT EXISTS \
last_mod_elemento_'+usuario+' (elemento text, last_mod text)')
        cursor.execute("CREATE TABLE IF NOT EXISTS dead_files_"+usuario+" \
(element text, death_time text)")
        cursor.execute("SELECT * FROM last_mod_elemento_"+usuario+"")
        linhas = cursor.fetchall()
        # linhas
        try:
                i=0
                while 1:
                        nome = str(linhas[i][0])
                        conn.send(nome)
                        sleep(1)
                        ult_mod = str(linhas[i][1])
                        conn.send(ult_mod)
                        sleep(1)
                        i=i+1
        except:
                conn.send('Fim')
                # 'Fim'
        while 1:
                answer = conn.recv(1024)
                print 'Se for 0 ta so no cliente, se for 1 so no serv'
                print answer

                if answer == '0':
                        compare_onlyclient(usuario,nome_pasta,)
                        print'Recebido do cliente\n'

                elif answer == '1':
                        compare_onlyserver(usuario,nome_pasta,)
                        print'Enviado para cliente\n'
                else:
                        break
                
def atualiza_pasta(usuario):
        nome_pasta = './My_Dropbox_'+usuario
        check_mod="SELECT * FROM dados_"+usuario+" WHERE usuario = ?"
        for row in cursor.execute(check_mod,(usuario,)):
                print row[0]+' '+row[2]
                print'enviando ultima modificacao da pasta q \
consta aqui no servidor\n'
                conn.send(row[2])
                sleep(1)
                actual_mod_time = conn.recv(1024)
                print actual_mod_time
                if row[2] != actual_mod_time:
                        pasta_modificada(nome_pasta,usuario,)
                #p1 = Process(target = recebe_de_cliente, args = (nome_pasta,))

        
def cadastrado(usuario):
        senha = conn.recv(1024)
        check_cadastro="SELECT * FROM dados_"+usuario+" WHERE usuario = ? and senha\
= ?"
        
        for row in cursor.execute(check_cadastro, (usuario,senha,)):
                if row[0]==usuario and row[1]==senha:
                        conn.send('Usuario Autenticado\nVoce esta logado')
                        sleep(1)
                        atualiza_pasta(usuario)
                        break
        conn.close()
        print'Sincronizacao feita com '+usuario+'!'
        #conn.send('Usuario ou senha incorretos!')

def novocadastro():
        usuario_novo = conn.recv(1024)
        senha_nova = conn.recv(1024)
        first_mod = conn.recv(1024)
        cursor.execute('CREATE TABLE IF NOT EXISTS dados_'+usuario_novo+' (usuario text, senha text, ultima_mod text)')
        cursor.execute("INSERT INTO dados_"+usuario_novo+" (usuario,senha,ultima_mod) VALUES (?,?,?)", (usuario_novo,senha_nova,first_mod))
        nome_pasta='./My_Dropbox_'+usuario_novo
        os.mkdir(nome_pasta)
        data_bank.commit()

def aceita(conn):
        while 1:
                print 'Connected by', addr
                resp_cadas = conn.recv(1024)
                if resp_cadas != '0':
                        cadastrado(resp_cadas)
                        conn.close() #Fecha conexão
                        break
                else:
                        novocadastro()
	
HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 50005              # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #IPv4,tipo de socket
s.bind((HOST, PORT)) #liga o socket com IP e porta

data_bank = sqlite3.connect('usuarios_servidor.db')
cursor = data_bank.cursor()


while(1):
	s.listen(5) #espera chegar pacotes na porta especificada
	conn, addr = s.accept()#Aceita uma conexão
	print "Aceitou mais uma"
	t = Process(target=aceita, args=(conn,))
	t.start()

