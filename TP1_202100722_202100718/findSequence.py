
from functools import reduce

def numeroIteracoes(primos):
    return reduce(lambda x, y: x * y, primos, 1)

def arrayResto(arrPrimos, i):
    return [(i % primo) for primo in arrPrimos]

#primos até ao que queremos incluir nos saltos
arrPrimos = [2,3,5,7]

it = numeroIteracoes(arrPrimos)

restos = [arrayResto(arrPrimos, i) for i in range(arrPrimos[-1], it + arrPrimos[-1])]
saltos = [0] * len(restos)    
    
restoSelecionado = 0

while(0 in restos[restoSelecionado]):
        restoSelecionado += 1

while(saltos[restoSelecionado] == 0):
    proximoSalto = 1
    
    while(0 in restos[(restoSelecionado + proximoSalto) % len(restos)]):
        proximoSalto += 1

    saltos[restoSelecionado] = proximoSalto
    restoSelecionado = (restoSelecionado + proximoSalto) % it

#for resto, salto in zip(restos, saltos):
    #print(resto, " - ", salto)
    
saltos = [x for x in saltos if x != 0]

print(saltos)


