# -*- coding: cp1252 -*-
# Echo client program
import socket,os
from time import sleep, time
from multiprocessing import Process
import sqlite3

def compara_sonocliente(sonocliente,after,nome_pasta,usuario,):
    print "Ta aqui e nao ta no servidor: ", ", ".join (sonocliente)
    tamanho_sonocliente = str(len(sonocliente))
    client.send(tamanho_sonocliente)
    sleep(1)
    for arq in sonocliente:
        client.send(arq)#Checa se no sevido há um arquivo morto com esse 
        sleep(1)
        tala = int(client.recv(1024))
        if tala:
            os.remove(nomepasta+'/'+arq)
            data_morte = str(time())
            cursor.execute("INSERT INTO arquvio_morto_"+usuario+" (elemento,data_morte) VALUES (?,?)", (arq,data_morte,))
            cursor.execute("DELETE FROM last_mod_"+usuario+" WHERE elemento = ?", (arq,))            
        else:
            #Algoritmo de envio de arquivo por socket foi tirado de http://stackoverflow.com/questions/9382045/send-a-file-through-sockets-in-python
            client.send(arq)
            sleep(1)
            umav = str(after[arq])
            client.send(umav)
            sleep(1)
            # nome_pasta+'/'+nome
            abre = open(nome_pasta+'/'+arq, "rb")
            tam = os.stat(nome_pasta+'/'+arq)[6]
            client.send(str(tam))
            sleep(1)
            if tam:
                l = abre.read(tam)
                client.send(l)
                sleep(1)
                abre.close()

def compara_sonoservidor(sonoservidor,before,nome_pasta,usuario,):
    print "Ta no servidor e nao ta aqui: ", ", ".join (sonoservidor)
    tamanho_sonoservidor = str(len(sonoservidor))
    client.send(tamanho_sonoservidor)
    sleep(1)
    for arq in sonoservidor:
        client.send(arq)
        sleep(1)
        for arq_morto in cursor.execute("SELECT * FROM \
arquivo_morto_"+usuario+" WHERE elemento = ?", (arq,)):
            exists = 1
        try:
            if exists:
                client.send('1')
                sleep(1)
        except:   
            client.send('0')
            sleep(1)
            nome_arq_novo = arq
            ult_mod_arq_novo = str(before[arq])
            tam_arq_novo = client.recv(1024)
            tam_arq_novo = int(tam_arq_novo)
            cursor.execute("INSERT INTO last_mod_elemento_"+usuario+" \
(elemento,last_mod) VALUES (?,?)", (nome_arq_novo,ult_mod_arq_novo,))
            banco_dados.commit()
            recebe=open(nome_pasta+'/'+nome_arq_novo,'wb')
            if tam_arq_novo:
                l = client.recv(tam_arq_novo)
                recebe.write(l)
                recebe.close()
    
    
def pasta_modificada(nome_pasta,usuario,):
#esqueleto do algoritmo de atualizacao de pagina foi tirado de: http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html
    before = {}
    after = {}
    while 1:
        arquivo1 = client.recv(1024)
        if arquivo1 == 'Fim':
            break
        else:
            ult_mod = client.recv(1024)
            before[arquivo1] = ult_mod
    cursor.execute("SELECT * FROM last_mod_elemento_"+usuario+"")
    existentes = cursor.fetchall()
    print existentes
    try:
        i=0
        while 1:
            nome = str(existentes[i][0])
            print nome
            ult_mod = str(existentes[i][1])
            after[nome] = ult_mod
            i=i+1
    except:
            print'Fim'
    print 'Antes: ',before
    sleep(1)
    print 'Depois: ',after
    sonocliente = [f for f in after if not f in before]
    sleep(1)
    sonoservidor = [f for f in before if not f in after]
    sleep(1)
    for f in after:
        try:
            if before[f]:
                if after[f] != before[f]:
                    print'sonoclientedated: ',f
                    sleep(1)
        except:
            sleep(1)
    
    if sonocliente:
        client.send('0')
        sleep(1)
        compara_sonocliente(sonocliente,after,nome_pasta,usuario,)
    
        
    if sonoservidor:
        client.send('1')
        sleep(1)
        compara_sonoservidor(sonoservidor,before,nome_pasta,usuario,)

    client.send('cabo')
    sleep(1)

        
    #before = after
        

def atualiza_pasta(usuario,ultima_mod,nome_pasta,):
    tempo_mod_constaservidor = client.recv(1024)
    print'Ultima modificacao q consta no servidor recebida\n'
    tempo_mod_atual = ultima_mod
    print'mod Servidor: '+tempo_mod_constaservidor
    print 'mod cliente: '+tempo_mod_atual
    if tempo_mod_atual != tempo_mod_constaservidor:
        print'\nPasta modificada\nAtualizando com o servidor..'
        client.send(tempo_mod_atual)
        sleep(1)
        pasta_modificada(nome_pasta,usuario)
        #mod_time_before = mod_time_after
    



def varre_pasta(usuario,nome_pasta,):
    cursor.execute('CREATE TABLE IF NOT EXISTS last_mod_elemento_'+usuario+' (elemento text, last_mod text)')
    cursor.execute('CREATE TABLE IF NOT EXISTS arquivo_morto_'+usuario+' (elemento text, data_morte text)')
    cursor.execute("SELECT * FROM last_mod_elemento_"+usuario+"")
    existentes = cursor.fetchall()
    before = {}
    try:
        i=0
        while 1:
            nome = str(existentes[i][0])
            ult_mod = str(existentes[i][1])
            before[nome] = ult_mod
            i=i+1
    except:
        print'Fim'
    print'Atualizando sem comunicar com o servidor. Atualizando ou definindo parametros\n'
    
    after = dict ([(f, str(os.stat(nome_pasta+'/'+f)[9])) for f in os.listdir (nome_pasta)])
    print before
    print after
    added = [f for f in after if not f in before]
    removed = [f for f in before if not f in after]
    for f in after:
        try:
            if before[f]:
                if after[f] != before[f]:
                    print'Atualizado: ',f
                    sleep(1)
        except:
            sleep(1)
    if added:
        print "Adicionado: ", ", ".join (added)
        for f in added:
            cursor.execute("INSERT INTO last_mod_elemento_"+usuario+" (elemento,last_mod) VALUES (?,?)", (str(f),str(after[f]),))
    if removed:
        print "Removido: ", ", ".join (removed)
        for f in before:
            cursor.execute("INSERT INTO arquvio_morto_"+usuario+" (elemento,last_mod) VALUES (?,?)", (f,before[f],))  
    banco_dados.commit()  
    print 'Acabou a varredura local\n'
    return(str(os.stat(nome_pasta)[8]))

def cadastrado(usuario):   
    senha=raw_input()    
    client.send(senha)
    sleep(1)
    print client.recv(1024)
    nome_pasta = './My_Dropbox_'+usuario
    nome_pasta_comp = 'My_Dropbox_'+usuario
    pasta_existente = os.listdir('.')
    print pasta_existente
    print len(pasta_existente)
    i=0
    if len(pasta_existente) == 0:
        os.mkdir(nome_pasta)
        print'Por conta de seu primeiro acesso, uma pasta foi criada onde voce\
rodou o programa para possibilitar o uso do seu Dropbox\n'
        cursor.execute('CREATE TABLE IF NOT EXISTS dados_'+usuario+'\
(usuario text, senha text, ultima_mod_pasta text)')
    for arq_dir in pasta_existente:
        i=i+1
        print i
        if arq_dir == nome_pasta_comp:
            break
        elif i == len(pasta_existente):
            os.mkdir(nome_pasta)
            print'Por conta de seu primeiro acesso, uma pasta foi criada onde voce\
rodou o programa para possibilitar o uso do seu Dropbox\n'
            cursor.execute('CREATE TABLE IF NOT EXISTS dados_\
'+usuario+' (usuario text, senha text, ultima_mod_pasta text)')
    ultima_mod = varre_pasta(usuario,nome_pasta,)
    cursor.execute("INSERT INTO dados_"+usuario+"\
(ultima_mod_pasta) VALUES (?)", (ultima_mod,))
    atualiza_pasta(usuario,ultima_mod,nome_pasta,)
    
def cria_usuario():
    usuario_novo = raw_input('Digite o nome de usuario desejado: ')
    client.sendall(usuario_novo)
    sleep(1)
    senha_novo = raw_input('Digite a senha desejada: ')
    client.sendall(senha_novo)
    sleep(1)
    print 'Usuario cadastrado'
    nome_pasta='./My_Dropbox_'+usuario_novo
    os.mkdir(nome_pasta)
    cursor.execute('CREATE TABLE IF NOT EXISTS dados_'+usuario_novo+'\
(usuario text, senha text, ultima_mod_pasta text)')
    print'Por conta de seu primeiro acesso, uma pasta foi criada onde voce\
rodou o programa para possibilitar o uso do seu Dropbox\n'
    primeira_mod = varre_pasta(usuario_novo,nome_pasta,)
    client.sendall(primeira_mod)
    sleep(1)
    cursor.execute("INSERT INTO dados_"+usuario_novo+"\
(usuario,senha,ultima_mod_pasta)\
VALUES (?,?,?)", (usuario_novo,senha_novo,primeira_mod))
    banco_dados.commit()

def entrada():
    print 'Conectado ao servidor\n\n'
    sleep(0.5)
    #'.'
    sleep(0.5)
    #'.'
    sleep(0.5)
    #'.\n\n'
    print'Digite seu usuario e sua senha\nCaso nao seja cadastrado, digite 0'
    resp_entrada=raw_input() #Só envia depois de apertar ENTER
    client.send(resp_entrada)
    sleep(1)
    return(resp_entrada)
    
#algoritmo de estabelecimento de socket e de inicio de processo tirado dos exemplos da professora
HOST = '192.168.25.39'    # The remote host
PORT = 50005              # The same port as used by the server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #IPv4,tipo de socket
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client.connect((HOST, PORT))  #Abre uma conexão com IP e porta especificados

banco_dados = sqlite3.connect('usuarios_cliente.db')
cursor = banco_dados.cursor()


while(1):
    resp_entrada=entrada()

    if resp_entrada != '0':
        autenticado=cadastrado(resp_entrada)
        break
    else:
        cria_usuario()
    
client.close() #Termina conexão
print "\n\nFechou a conexao"
