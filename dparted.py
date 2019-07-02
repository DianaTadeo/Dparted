#!/bin/etc/python

import sys
import optparse
import os

SECTOR_SIZE=512
PART_TYPES = "\n0) Empty \n7) HPFS/NTFS/ExFAT \n83) Linux \n82) Linux swap/Solaris \n86) NTFS volume Set\n"
prim=0
TOTBYTES=1048576

def opciones():
	"""
	Permite verificar la opci[on -l para listar las particiones en el disco de forma externa
	"""
	parser = optparse.OptionParser()
	parser.add_option('-l','--listar', dest='listar', action='store_true', default=None, help='Para listar las particiones de un dispositivo')
	opts,args = parser.parse_args()
	return opts
    
def menu():
	"""
	Despliega el menu que aparecera para la interaccion con el usuario
	"""
	print "i) Mostrar informacion del dipositivo"
	print "n) Crear nueva particion"
	print "p) Imprimir tabla de particones"
	print "w) Guardar"
	print "q) Salir"
	res= raw_input("\nElige la opcion: ")
	return res

def read_parts(mbr):
	"""
	Permite leer la tabla de partciones y asi distinguir las partes ya presentes
	en el dispositivo.
	Solo lee si las contine, de lo contrario, la lista es 0
	Devuelve una lista con el contenido de la tabla mbr de acuerdo a las particones.
	"""
	j = 0
	parts = []
	for i in range(4):
		# opcion que permite saber si el mbr tiene contenido
		if int("".join(mbr[j+8:j+12][::-1]).encode('hex'), 16) !=0: 
			new_part= []
			#Para la lectura de cada byte
			new_part.append(int("".join(mbr[j+8:j+12][::-1]).encode('hex'), 16))
			new_part.append(int("".join(mbr[j+12:j+16][::-1]).encode('hex'), 16))
			new_part.append(int(hex(ord(mbr[j+4]))[2:], 16))
			parts.append(new_part)
			j = j+16
	
	return parts
	
def display_MBR(parts):
	"""
	Esta funcion muestra el contenido de forma legible de la tabla mbr
	de acuerdo [unicamente a las particiones que son aceptadas por este programa.
	Si se intenta leer otro dispositivo con algun tipo de partcion que no sea alguno
	de los enumerados en el programa, no se podra leer.
	"""
	types= {0:'Empty', 7:"HPFS/NTFS/ExFAT", 130:"Linux Swap/Solaris", 131:"Linux", 134:"NTFS volume Set" }
	print ""
	cont = 1
	if len(parts)==0:
		print "No hay particiones"
	else:
		print "	Device       Start      End     Sectors     Size      Type"
		#Por cada particion
		for part in parts:
			print "	/dev/sdb"+str(cont)+"    "+str(part[0])+"      "+str(part[0]+part[1]-1)+"     "+str(part[1])+"   "+str((part[1]*SECTOR_SIZE)/(1024*1024))+"MB      "+types[part[2]]
			cont = cont+1	
	print "\n"
			
def mov(part):
	hexa = []
	byte4 = '{:08x}'.format(part)
	for i in range(8):
		if (i+1)%2!=0:
			byte = str(byte4[i])
		else:
			byte = byte+str(byte4[i])
			hexa.append(byte)	
	return hexa[::-1]
	
def write_MBR(parts):
	"""
	Permite escribir los cambios dentro del dispositivo.
	Escribe el formato de la tabla mbr con las particiones que
	fueron creadas o modificadas, haciendolo legible tambien
	para la herramienta fdisk.
	"""
	with open(sys.argv[1], "r+b") as dev:
		dev.seek(446, 0)
		for part in parts:
			#Por cada particion para recorrer la tabla mbr
			dev.seek(2, 1) 
			dev.write(chr(0)) #flag
			dev.write(chr(0)) #cabecera
			dev.write(chr(part[2])) #tipo
			dev.seek(3, 1)
			#Se seleccionan los bytes dentro para 
			byte_sectors=mov(part[1])
			byte_blocks=mov(part[1])
			for byte in byte_sectors:
				dev.write(chr(int(byte, 16)))
			for byte in byte_blocks:
				dev.write(chr(int(byte, 16)))
	#Para escribir el final de la tabla mbr
	with open(sys.argv[1], "r+b") as dev:
		dev.seek(510, 0)
		dev.write('\x55\xaa')

               
if __name__ == '__main__':
	prim=0
	opts= opciones()
	if len(sys.argv)==1:
		print "Se tiene que elegir un dispositivo"
		exit(1)
	with open(sys.argv[1], "rb") as dev:
		dev.seek(0, 2)
		dev_size = dev.tell()/SECTOR_SIZE
		info="Sector Size: 512 bytes\nTotal Blocks: "+str(dev_size)
		dev.seek(446, 0)
		mbr = list(dev.read(64))
		
	parts=read_parts(mbr)
	if opts.listar:
		print info
		display_MBR(parts)
		exit(0);

	while(1):
		option=menu()
		if option=="i":
			print info+ "\n"
		elif option=="p": #Imprimir tabla MBR
			display_MBR(parts)		
		elif option=="w": #Guardar cambios
			write_MBR(parts)
		elif option=="q": #Salir
			exit(0)
		elif option=="n": #Agregar una nueva particion
			if prim==4:
				print "No hay particiones primarias disponibles.\n"
			else:
				#Creacion de las particiones
				
				free_space = 0
				for part in parts:
					free_space = free_space + part[1]
				sec_inicial = 2048
				size_pred = 0
				for part in parts:
					sec_inicial = part[1]+sec_inicial
					size_pred = part[1] + size_pred
				#para cacular el espacio a ocupar
				
				size_pred = dev_size - size_pred
				defsize=(size_pred*SECTOR_SIZE)/TOTBYTES #valor predefinido
				#se define la nueva particion
				n_part = []
				print "\nParticion " + str(len(parts))
				
				sec_ini=raw_input("Sector Inicial ("+str(sec_inicial)+"-"+str(dev_size)+", default "+str(sec_inicial)+"):")
				size=raw_input("Tamaoo en MB, default "+str(defsize)+"): ")

				size_pred=size if len(size)>0 else defsize
				sec_inicial=sec_ini if len(sec_ini)>0 else sec_inicial
				size_pred = (int(size_pred)*TOTBYTES)/SECTOR_SIZE
				print PART_TYPES
				#Se da la opci[on de la particion al usuario
				
				ptype=raw_input("Elige el tipo de particion: ")
				if ptype=="0" or ptype=="7" or ptype=="82" or ptype=="83" or ptype=="86":
					n_part.append(int(sec_inicial)) #sector de inicio
					n_part.append(int(size_pred)) #cilindro (tamanio)
					n_part.append(int(ptype, 16))
					parts.append(n_part)
					print "Se ha creado la particion.\n"
					prim+=1
				else:
					print" El tipo de particion no fue valido\n"
		else:
			print "Es a es una opcion no valida\n"
