import pandas as pd 
# LMT : Quité src en la línea que sigue
from DataProcessing.transform_data import hora_a_minutos
from pathlib import Path


def lectura_tablas_c4_c6(ruta,hoja):
    base = pd.read_excel(ruta,skiprows=2,sheet_name=hoja)
    base = base[['ORD', 'ACC.', 'COD. OP.', 'CIRCUITO', 'HORA SALIDA QUITUMBE', 
        'HORA LLEGADA MAYORISTA', 'HORA LLEGADA RECREO', 'HORA LLEGADA STO. DOMINGO',
        'HORA LLEGADA COLÓN','HORA LLEGADA QUITUMBE', 'ARRIBO QUITUMBE', 'INTERVALO',
        'TIEMPO EN ANDÉN']]
    base = base[['ORD','COD. OP.','CIRCUITO','HORA SALIDA QUITUMBE','HORA LLEGADA QUITUMBE']]
    base.columns = ['ORD','COD. OP.','CIRCUITO','SALIDA','LLEGADA']
    return base

def transformacion_a_minutos(base):
    baseModified=base.copy()
    baseModified.dropna(subset='ORD',inplace=True)
    baseModified['SALIDA'] = baseModified['SALIDA'].apply(hora_a_minutos)
    baseModified['LLEGADA'] = baseModified['LLEGADA'].apply(hora_a_minutos)
    return baseModified


def costoA2(costo):
    if costo < 25:
        return 25 - costo
    elif costo > 35:
        return costo - 35
    else:
        return 0
    
def creacion_arcos_A1_A2(base,l1,u1,l2,u2):
    baseArcos = base.copy()
    arcos_costo_A1 = []
    arcos_costo_A2 = []
    arcos_costo = []
    for i in baseArcos.iterrows():
        hora_llegada = i[1]['LLEGADA']
        
        base_filtrada_A1 = baseArcos[
            (l1<=baseArcos['SALIDA']-hora_llegada) & (baseArcos['SALIDA']-hora_llegada<=u1)
        ]
        
        base_filtrada_A1 = pd.DataFrame({'ORD':base_filtrada_A1['ORD'],'SALIDA':(base_filtrada_A1['SALIDA'] - hora_llegada)}).reset_index()
        base_filtrada_A1['Arco-Costo A1'] = base_filtrada_A1.apply(lambda row: (row['ORD'], row['SALIDA']), axis=1)
        arcos_costo_A1.append(base_filtrada_A1['Arco-Costo A1'].tolist())

        base_filtrada_A2 = baseArcos[
            (l2<=baseArcos['SALIDA']-hora_llegada) & (baseArcos['SALIDA']-hora_llegada<=u2)
        ]
        costoA2Serie = (base_filtrada_A2['SALIDA'] - hora_llegada).apply(costoA2)
        base_filtrada_A2 = pd.DataFrame({'ORD':base_filtrada_A2['ORD'],'SALIDA':costoA2Serie}).reset_index()
        base_filtrada_A2['Arco-Costo A2'] = base_filtrada_A2.apply(lambda row: (row['ORD'], row['SALIDA']), axis=1)
        arcos_costo_A2.append(base_filtrada_A2['Arco-Costo A2'].tolist())
        
        base_filtrada = baseArcos[baseArcos['SALIDA']>=hora_llegada]
        base_filtrada = pd.DataFrame(base_filtrada['SALIDA'] - hora_llegada).reset_index()
        base_filtrada['Arco-Costo'] = base_filtrada.apply(lambda row: (row['index']+1, row['SALIDA']), axis=1)
        arcos_costo.append(base_filtrada['Arco-Costo'].tolist())
    
    baseArcos['Arcos-Costo']=  pd.Series(arcos_costo)    
    baseArcos['Arcos-Costo A1']=  pd.Series(arcos_costo_A1)
    baseArcos['Arcos-Costo A2']=  pd.Series(arcos_costo_A2)
    return baseArcos



def tablas_sabados_c1(ruta,hoja):
    base = pd.read_excel(ruta,skiprows=1,sheet_name=hoja)
    recreo_sur_norte = base[['ORD', 'ACC.', 'COD. OP.', 'CIRCUITO', 'HORA SALIDA RECREO', 
        'HORA LLEGADA STO DOMINGO', 'HORA LLEGADA EJIDO', 'HORA LLEGADA COLÓN',
        'HORA LLEGADA LABRADOR', 'ARRIBO RECREO', 'INTERVALO',
        'TIEMPO EN ANDÉN']]
    labrador_norte_sur = base[['ORD.1', 'ACC..1', 'COD. OP..1',
       'CIRCUITO.1', 'HORA SALIDA LABRADOR', 'HORA LLEGADA COLÓN.1',
       'HORA LLEGADA EJIDO.1', 'HORA LLEGADA STO DOMINGO.1',
       'HORA LLEGADA RECREO', 'ARRIBO LABRADOR', 'INTERVALO.1',
       'TIEMPO EN ANDÉN.1']]
    labrador_norte_sur.columns = ['ORD', 'ACC.', 'COD. OP.', 'CIRCUITO', 'HORA SALIDA RECREO',
       'HORA LLEGADA STO DOMINGO', 'HORA LLEGADA EJIDO', 'HORA LLEGADA COLÓN',
       'HORA LLEGADA LABRADOR', 'ARRIBO RECREO', 'INTERVALO',
       'TIEMPO EN ANDÉN']
    
    return recreo_sur_norte,labrador_norte_sur

def tablas_ordinarios_c1_c2(ruta,hoja):
    base = pd.read_excel(ruta,skiprows=1,sheet_name=hoja)
    recreo = base[['ORD', 'ACC.', 'COD. OP.', 'CIRCUITO', 'HORA SALIDA RECREO',
        'HORA LLEGADA LABRADOR', 'INTERVALO',
        'TIEMPO EN ANDÉN']]
    recreo.columns = ['ORD', 'ACC.', 'COD. OP.', 'CIRCUITO', 'HORA_SALIDA',
        'HORA_LLEGADA', 'INTERVALO',
        'TIEMPO EN ANDÉN']
    recreo['TERMINAL'] = 'RECREO'
    recreo.dropna(subset='ORD',inplace=True)
    labrador = base[['ORD.1', 'ACC..1', 'COD. OP..1',
        'CIRCUITO.1', 'HORA SALIDA LABRADOR', 
        'HORA LLEGADA RECREO', 'INTERVALO.1',
        'TIEMPO EN ANDÉN.1']]
    labrador.columns = ['ORD', 'ACC.', 'COD. OP.', 'CIRCUITO', 'HORA_SALIDA',
        'HORA_LLEGADA', 'INTERVALO',
        'TIEMPO EN ANDÉN']
    labrador['TERMINAL'] = 'LABRADOR'
    labrador.dropna(subset='ORD',inplace=True)
    base = pd.concat([recreo,labrador]).reset_index(drop=True).reset_index()
    base.columns = ['ID', 'ORD', 'ACC.', 'COD. OP.', 'CIRCUITO', 'HORA_SALIDA',
        'HORA_LLEGADA', 'INTERVALO', 'TIEMPO EN ANDÉN', 'TERMINAL']
    base['ID'] = base['ID']+1
    base['HORA_LLEGADA'] = base['HORA_LLEGADA'].apply(hora_a_minutos)
    base['HORA_SALIDA'] = base['HORA_SALIDA'].apply(hora_a_minutos)
    return base

def tablas_ordinarios_c2(ruta,hoja):
    base = pd.read_excel(ruta,skiprows=3,sheet_name=hoja)
    base = base[['ORD', 'ACC.', 'COD. OP.', 'CIRCUITO', 'HORA SALIDA MORAN VAL',
            'HORA LLEGADA LABRADOR', 'INTERVALO',
            'TIEMPO EN ANDÉN']]
    base.columns = ['ORD', 'ACC.', 'COD. OP.', 'CIRCUITO', 'HORA_SALIDA',
            'HORA_LLEGADA', 'INTERVALO',
            'TIEMPO EN ANDÉN']
    base['TERMINAL'] = 'MORAN'
    base.dropna(subset='ORD',inplace=True)
    base = base.reset_index(drop=True).reset_index()
    base.columns = ['ID', 'ORD', 'ACC.', 'COD. OP.', 'CIRCUITO', 'HORA_SALIDA',
        'HORA_LLEGADA', 'INTERVALO', 'TIEMPO EN ANDÉN', 'TERMINAL']
    base['ID'] = base['ID']+1
    base['HORA_LLEGADA'] = base['HORA_LLEGADA'].apply(hora_a_minutos)
    base['HORA_SALIDA'] = base['HORA_SALIDA'].apply(hora_a_minutos)
    return base 

def tablas_sabados_c4_c6(ruta,hoja):
    base = pd.read_excel(ruta,skiprows=4,sheet_name=hoja)
    quitumbe_sur_norte = base[['ORD', 'ACC.', 'COD. OP.', 'CIRCUITO', 'HORA SALIDA QUITUMBE', 
        'HORA LLEGADA MAYORISTA', 'HORA LLEGADA RECREO', 'HORA LLEGADA STO. DOMINGO',
        'HORA LLEGADA COLÓN','HORA LLEGADA QUITUMBE', 'ARRIBO QUITUMBE', 'INTERVALO',
        'TIEMPO EN ANDÉN']]
    quitumbe_sur_norte.dropna(subset='ORD',inplace=True)
    return quitumbe_sur_norte

def tablas_ordinarios_c4_c6(ruta,hoja):
    base = pd.read_excel(ruta,skiprows=2,sheet_name=hoja)
    quitumbe_sur_norte = base[['ORD', 'ACC.', 'COD. OP.', 'CIRCUITO', 'HORA SALIDA QUITUMBE', 
        'HORA LLEGADA MAYORISTA', 'HORA LLEGADA RECREO', 'HORA LLEGADA STO. DOMINGO',
        'HORA LLEGADA COLÓN','HORA LLEGADA QUITUMBE', 'ARRIBO QUITUMBE', 'INTERVALO',
        'TIEMPO EN ANDÉN']]
    quitumbe_sur_norte.dropna(subset='ORD',inplace=True)
    quitumbe_sur_norte['HORA SALIDA QUITUMBE MINUTOS'] = quitumbe_sur_norte['HORA SALIDA QUITUMBE'].apply(hora_a_minutos)
    quitumbe_sur_norte['HORA LLEGADA QUITUMBE MINUTOS'] = quitumbe_sur_norte['HORA LLEGADA QUITUMBE'].apply(hora_a_minutos)
    return quitumbe_sur_norte


def tablas_ordinarios_c4_c6_v2(ruta,hoja):
    base = pd.read_excel(ruta,sheet_name=hoja)
    base = base.reset_index()
    columnas = list(base.columns)
    columnas[0] = 'ID'
    base.columns = columnas
    base['ID'] = base['ID'] +1
    quitumbe_sur_norte = base[['ID','ORD', 'ACC.', 'COD. OP.', 'CIRCUITO', 'HORA SALIDA ǪUITUMBE', 
        'HORA LLEGADA ǪUITUMBE','TIEMPO EN ANDÉN']]
    quitumbe_sur_norte['HORA_SALIDA'] = quitumbe_sur_norte['HORA SALIDA ǪUITUMBE'].apply(hora_a_minutos)
    quitumbe_sur_norte.dropna(subset='ORD',inplace=True)
    quitumbe_sur_norte['HORA_LLEGADA'] = quitumbe_sur_norte['HORA LLEGADA ǪUITUMBE'].apply(hora_a_minutos)
    return quitumbe_sur_norte

def tablas_ordinarios_c4_c6_v2(ruta,hoja):
    base = pd.read_excel(ruta,sheet_name=hoja)
    base = base.reset_index()
    columnas = list(base.columns)
    columnas[0] = 'ID'
    base.columns = columnas
    base['ID'] = base['ID'] +1
    quitumbe_sur_norte = base[['ID','ORD', 'ACC.', 'COD. OP.', 'CIRCUITO', 'HORA SALIDA ǪUITUMBE', 
        'HORA LLEGADA ǪUITUMBE','TIEMPO EN ANDÉN']]
    quitumbe_sur_norte['HORA_SALIDA'] = quitumbe_sur_norte['HORA SALIDA ǪUITUMBE'].apply(hora_a_minutos)
    quitumbe_sur_norte.dropna(subset='ORD',inplace=True)
    quitumbe_sur_norte['HORA_LLEGADA'] = quitumbe_sur_norte['HORA LLEGADA ǪUITUMBE'].apply(hora_a_minutos)
    return quitumbe_sur_norte


def lectura_alimentadora_norte(ruta, hoja):
    
    from pathlib import Path
    # LMT : Quité src en la línea que sigue
    from DataProcessing.transform_data import hora_a_minutos
    base = pd.read_excel(ruta, sheet_name=hoja, header=4)
    
    # Extract the name of the Excel file without extension for CIRCUITO
    import os
    nombre_archivo = os.path.basename(ruta)
    circuito = os.path.splitext(nombre_archivo)[0]
    
    # Create the dataframe with the requested columns
    df_resultado = pd.DataFrame()
    
    # Map the requested columns from the original data
    df_resultado['ORD'] = base['INDEX']
    df_resultado['COD. OP.'] = base['TURNO']
    df_resultado['CIRCUITO'] = circuito  # Using the filename as CIRCUITO
    df_resultado['HORA SALIDA'] = base['HORA SALIDA']
    df_resultado['HORA LLEGADA'] = base['HORA LLEGADA']
    df_resultado['TIEMPO EN ANDÉN'] = base['T DESPACHO']
    
    # Convert time columns to minutes
    df_resultado['HORA_SALIDA'] = df_resultado['HORA SALIDA'].apply(hora_a_minutos)
    df_resultado['HORA_LLEGADA'] = df_resultado['HORA LLEGADA'].apply(hora_a_minutos)
    
    
    
    return df_resultado

def obtener_rutas_carros(m1):
    """
    Obtiene un diccionario con las rutas completas de cada carro
    m1: modelo de Gurobi resuelto
    """
    # Primero obtenemos todos los arcos que son 1 en la solución
    arcos_activos = []
    for v in m1.getVars():
        if v.varName.startswith('x[') and v.x > 0.5:
            indices = v.varName[2:-1].split(',')
            i, j = int(indices[0]), int(indices[1])
            arcos_activos.append((i, j))
    
    # Diccionario para almacenar las rutas
    rutas = {}
    carro_actual = 1
    
    # Mientras queden arcos por asignar
    while arcos_activos:
        # Buscamos un arco que salga del depósito (0)
        ruta_actual = []
        for arco in arcos_activos:
            if arco[0] == 0:
                ruta_actual.append(arco)
                arcos_activos.remove(arco)
                break
        
        # Si encontramos un arco inicial, seguimos la ruta
        if ruta_actual:
            while True:
                ultimo_nodo = ruta_actual[-1][1]
                # Buscamos el siguiente arco en la ruta
                siguiente_arco = None
                for arco in arcos_activos:
                    if arco[0] == ultimo_nodo:
                        siguiente_arco = arco
                        break
                
                if siguiente_arco:
                    ruta_actual.append(siguiente_arco)
                    arcos_activos.remove(siguiente_arco)
                else:
                    break
            
            # Guardamos la ruta completa en el diccionario
            rutas[carro_actual] = ruta_actual
            carro_actual += 1
    
    return rutas

def crear_dataframe_resultado(m1, df_viajes):
    """
    Crea un dataframe con la información de los viajes asignados a cada carro
    según la solución del modelo Gurobi.
    
    Parámetros:
    - m1: modelo Gurobi resuelto
    - df_viajes: dataframe con la información de los viajes (de lectura_alimentadora_norte)
    
    Retorna:
    - Un dataframe con la información de los viajes ordenados por carro
    """
    import pandas as pd
    import numpy as np
    
    # Obtener las rutas de los carros
    rutas_carros = obtener_rutas_carros(m1)
    
    # Diccionario para almacenar los costos de los arcos
    costos_arcos = {}
    
    # Extraer los costos (coeficientes objetivos) de las variables de decisión
    for v in m1.getVars():
        if v.varName.startswith('x['):
            # Extraer los índices del nombre de la variable
            indices = v.varName[2:-1].split(',')
            if len(indices) == 2:
                i, j = int(indices[0]), int(indices[1])
                # Guardar el coeficiente objetivo (costo) del arco
                costos_arcos[(i, j)] = v.Obj
    
    # Crear un dataframe vacío para almacenar los resultados
    columnas = ['ORD', 'COD. OP.', 'CIRCUITO', 'TIEMPO EN ANDÉN', 
               'HORA SALIDA', 'HORA LLEGADA', 'HORA_SALIDA', 'HORA_LLEGADA']
    resultado_df = pd.DataFrame(columns=columnas)
    
    # Reset index de df_viajes para poder acceder a ORD como columna si es necesario
    df_viajes_reset = df_viajes.reset_index() if df_viajes.index.name == 'ORD' else df_viajes.copy()
    
    # Procesar cada ruta de carro
    for carro, arcos in rutas_carros.items():
        for arco in arcos:
            origen, destino = arco
            
            # Ignorar arcos hacia el depósito final (500)
            if destino == 500:
                continue
            
            # El viaje actual es el destino del arco
            viaje = destino
            
            # Filtrar el dataframe original para obtener la fila del viaje
            if 'ORD' in df_viajes_reset.columns:
                fila_viaje = df_viajes_reset[df_viajes_reset['ORD'] == viaje]
            else:
                # Si ORD es el índice
                fila_viaje = df_viajes.loc[[viaje]] if viaje in df_viajes.index else pd.DataFrame()
                if not fila_viaje.empty:
                    fila_viaje = fila_viaje.reset_index()
            
            # Si encontramos el viaje, agregarlo al resultado
            if not fila_viaje.empty:
                # Obtener el tiempo en andén del arco que llega a este viaje
                tiempo_anden = costos_arcos.get((origen, destino), None)
                
                # Crear una nueva fila para el resultado
                nueva_fila = pd.DataFrame({
                    'ORD': [viaje],
                    'COD. OP.': [carro],  # Solo el número del carro
                    'CIRCUITO': [fila_viaje['CIRCUITO'].iloc[0]] if 'CIRCUITO' in fila_viaje.columns else [None],
                    'TIEMPO EN ANDÉN': [tiempo_anden],  # Tiempo del arco que llega a este viaje
                    'HORA SALIDA': [fila_viaje['HORA SALIDA'].iloc[0]] if 'HORA SALIDA' in fila_viaje.columns else [None],
                    'HORA LLEGADA': [fila_viaje['HORA LLEGADA'].iloc[0]] if 'HORA LLEGADA' in fila_viaje.columns else [None],
                    'HORA_SALIDA': [fila_viaje['HORA_SALIDA'].iloc[0]] if 'HORA_SALIDA' in fila_viaje.columns else [None],
                    'HORA_LLEGADA': [fila_viaje['HORA_LLEGADA'].iloc[0]] if 'HORA_LLEGADA' in fila_viaje.columns else [None]
                })
                
                # Añadir la nueva fila al dataframe de resultados
                resultado_df = pd.concat([resultado_df, nueva_fila], ignore_index=True)
    
    # Ordenar por ORD
    resultado_df = resultado_df.sort_values('ORD')
    
    # Establecer ORD como índice pero mantenerlo como columna también
    resultado_df.set_index('ORD', drop=False, inplace=True)
    
    return resultado_df