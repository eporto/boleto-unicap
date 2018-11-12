import urllib.parse, urllib.request
import re
import sys
from getpass import getpass

# Sinta-se livre pra mudar o que quiser e cagar o programa :)
ARQUIVO_GERADO	 = "Boleto"
UNICAP_BASE_URL  = "http://www.unicap.br/"
PORTAL_ALUNO_URL = "PortalGraduacao/AlunoGraduacao"

#########################
# Request
def doRequest(url,params=None, contentType=None):
	data = params
	if(data != None):
		if(type(data) != dict):
			raise Exception("Params precisa ser do tipo DICTIONARY")
		data = urllib.parse.urlencode(data)
		data = data.encode('utf-8')

	header = {}
	if(contentType != None):
		header = {"Content-Type": contentType}

	try:	
		req = urllib.request.Request(url, data, header)
		f = urllib.request.urlopen(req)
		return f.read()
	except Exception as error:
		print(error)
		sys.exit(1)

# Verifica se ao fazer a requisição o usuário ainda está logado
def isLoggedIn(html):
	return "modalError" not in html

#########################
# Obtém o nome do aluno -- DEBUG ONLY --
def getAluno(html):
	pass

#########################
# Faz um parse em uma String que representa uma página HTML. A string É a resposta de um doRequest()
def getJSessionID(html):
	jsessionRegEx = 'jsessionid=[a-zA-Z0-9]+'
	matchList = re.findall(jsessionRegEx, html)	
	# re.findall retorna uma list com todos os match. Em teoria se achar é pra ter só um elemento
	if( len(matchList) > 0 ):
		return re.sub('jsessionid=', '', matchList[0]) # Retiro a tag "jsessionid=" e fico só com o valor do token
	
#########################
# Faz login na unicap. O path é /PortalGraduacao/AlunoGraduacao
# Não precisa do JSessionID gerado na página inicial pois o mesmo é retornado como Cookie ao fazer login (além dele estar disponível também no HTML)
# Formato do JSessionID: <form id="loginPortal" method="post" name="formPortal" action="AlunoGraduacao;jsessionid=44D11D5646360653F440AB2351424EE8">
def unicapLogin(matricula, digito, senha):
	try:
		matricula = int(matricula)
		digito = int(digito)
		senha = int(senha)
	except Exception as error:
		print("Matricula e senha são números !")
		sys.exit(1)

	loginUrl = UNICAP_BASE_URL + PORTAL_ALUNO_URL
	dataLogin = { 'rotina' : 1, 'Matricula' : matricula, 'Digito' : digito, 'Senha' : senha }
	htmlResponse = doRequest(loginUrl, dataLogin, "application/x-www-form-urlencoded").decode('ISO-8859-1')

	if( isLoggedIn(htmlResponse) == False):
		print("Matricula e/ou Senha inválido(s)")
		sys.exit(1) # Se deu merda, fecha :)

	jsessionid = getJSessionID(htmlResponse)

	# Se deu alguma merda......
	if( jsessionid.strip() == ""):
		print("Erro ao pegar o JSESSIONID :(")
		sys.exit(1) # Se deu merda, fecha :)

	return jsessionid

#########################
# Os boletos estão em uma tabela de 4 colunas (Parcela, Vencimento, Valor, Situação)
# Quando o RegEX fizer a busca, irá retornar os valores das colunas como elementos de uma lista
# Ou seja, se eu tenho 5 boletos eu vou ter 20 elementos ( 5 boletos x 4 colunas )
def parseBoletoHTML(html):
	rowIdentifier = "<td class=\"center\">"
	boletoRegex = rowIdentifier+".*</td>" # Ex.: <td class= "center">31/08/2018</td> 
	matchList = re.findall(boletoRegex, html)

	# Se não encontrar nada, retorne
	if( len(matchList) == 0):
		return ""

	tdLen = len(rowIdentifier)
	boletos = []
	for i in range(0, len(matchList), 4):
		# lista de dictionaries
		boletos.append({
			"parcela" 	 : matchList[i][ tdLen : matchList[i].find("</td>") ], 	  # pegando os valores de cada elemento com um substring
			"vencimento" : matchList[i+1][ tdLen : matchList[i+1].find("</td>") ],
			"valor" 	 : matchList[i+2][ tdLen : matchList[i+2].find("</td>") ],
			"situacao" 	 : matchList[i+3][ tdLen : matchList[i+3].find("</td>") ]
		})

	return boletos

#########################
# Odeio esse português-inglês em programação
def getBoleto(jsessionid):
	boletoUrl = UNICAP_BASE_URL + PORTAL_ALUNO_URL + ";jsessionid=" + jsessionid
	dataBoleto = { 'rotina' : 24 }
	htmlBoleto = doRequest(boletoUrl, dataBoleto, "application/x-www-form-urlencoded").decode('ISO-8859-1')

	return parseBoletoHTML(htmlBoleto)

#########################
# Para baixar um boleto basta mandar a rotina junto com a parcela
# O que será retornado no RESPONSE BODY são os bytes que compoem o arquivo do boleto
def downloadBoleto(jsessionid, parcela):
	dataBoleto = { "rotina" : 201, "Parcela" : parcela }
	downloadUrl = UNICAP_BASE_URL + PORTAL_ALUNO_URL +  ";jsessionid=" + jsessionid
	
	return doRequest(downloadUrl, dataBoleto, "application/x-www-form-urlencoded")
	

########################################################
# 				   PROGRAM START					   #
########################################################
# http://www.unicap.br/PortalGraduacao -> Gera o JSESSIONID
# <form id="loginPortal" method="post" name="formPortal" action="AlunoGraduacao;jsessionid=69F0A10F70A29D07EA754AD554AE8A64">

# POST (LOGIN)
# http://www.unicap.br/PortalGraduacao/AlunoGraduacao;jsessionid=FA7FA7CBB9B0BE8B8E2235F634FF1611
# rotina=1&Matricula=XXXXX&Digito=Y&Senha=ZZZZZ

# POST (BOLETO)
# http://www.unicap.br/PortalGraduacao/AlunoGraduacao;jsessionid=FA7FA7CBB9B0BE8B8E2235F634FF1611
# rotina=24
# 

# POST (DOWNLOAD)
# rotina=201&Parcela=3

# RESPONSE HEADER - DOWNLOAD
# Connection: Keep-Alive
# Content-Disposition: filename='Boleto.pdf'
# Content-Type: application/pdf
# Date: Thu, 27 Sep 2018 16:41:57 GMT
# Keep-Alive: timeout=5, max=100
# Transfer-Encoding: chunked

# Caso queira logar direto só colocar os valores hardcoded e remover o INPUT() e o GETPASS()
MATRICULA_ALUNO = input("Matricula: ")
SENHA_ALUNO = getpass("Senha:")

token = unicapLogin(MATRICULA_ALUNO[0:-1], MATRICULA_ALUNO[-1], SENHA_ALUNO)

boletoList = getBoleto(token)

# Pego somente os que tão em aberto. Pq raios alguém quer ver até os pagos?
emAbertoList = list(filter(lambda boleto: "Aberto" in boleto["situacao"], boletoList))
print() # AQUELE BARRA ENI PRA DEIXAR MAIS BONITO

# Parabéns, você pagou tudo, continue assim (Exceto se você for daqueles que paga tudo e reprova sempre, aí _ _   _ _ _ _ _   _ _   _ _ (Preencha as lacunas - by Silvio))
if( len(emAbertoList) == 0 ):
	print("Parabéns, tudo pago >:D\nBye !")
	sys.exit(0)

print("Encontrado", len(emAbertoList), "boleto(s) em aberto !")

for boleto in emAbertoList:
	boletoData = downloadBoleto(token, boleto["parcela"])
	
	with open("{}-{}.pdf".format(ARQUIVO_GERADO, boleto['parcela']),'wb') as f: # fffffffffffffffffffffffffffffffffffffffffffffffffffffff adoro variáveis que se chamam "f"
		print("Baixando... Parcela: {} Vencimento: {} Valor: {} Situação: {}".format( boleto["parcela"], boleto["vencimento"], boleto["valor"], boleto["situacao"].upper() ) )
		f.write(boletoData)

# NÃO UTILIZADO MAIS
# print("Encontrado", len(boletoList), "parcela(s)")
# for i, boleto in enumerate(boletoList):
# 	print( "{} - Parcela: {} Vencimento: {} Valor: {} Situação: {}".format( i, boleto["parcela"], boleto["vencimento"], boleto["valor"], boleto["situacao"].upper() ) )

# 	# Boleto em aberto baixa !
# 	if("Aberto" in boleto["situacao"]):
# 		boletoData = downloadBoleto(token, boleto["parcela"])
# 		with open("{}-{}.pdf".format(ARQUIVO_GERADO, boleto['parcela']),'wb') as f: 
# 			print("Baixando...Parcela:", boleto["parcela"])
# 			f.write(boletoData)