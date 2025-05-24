import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Optional, Dict, Tuple
import gurobipy as gp
import numpy as np
import datetime

def procesar_solucion_modelo(modelo, viajes_df) -> pd.DataFrame:
    """
    Procesa la solución del modelo para crear un DataFrame con las rutas de las unidades.
    
    Args:
        modelo: Modelo de Gurobi resuelto
        viajes_df: DataFrame con la información de los viajes
        
    Returns:
        pd.DataFrame: DataFrame con las rutas de las unidades
    """
    print(f"Procesando solución del modelo...")
    print(f"Viajes disponibles: {viajes_df.shape}")
    print(f"Columnas en viajes_df: {viajes_df.columns.tolist()}")
    
    # Verificar y ajustar formato de tiempo si es necesario
    if 'HORA_SALIDA' in viajes_df.columns and 'HORA_LLEGADA' in viajes_df.columns:
        # Si son solo horas sin fecha, añadir una fecha ficticia para facilitar cálculos
        if not pd.api.types.is_datetime64_dtype(viajes_df['HORA_SALIDA']):
            try:
                # Si es formato de hora (HH:MM o similar)
                if isinstance(viajes_df['HORA_SALIDA'].iloc[0], str) and ':' in viajes_df['HORA_SALIDA'].iloc[0]:
                    print("Convirtiendo horas a formato datetime...")
                    base_date = pd.Timestamp('2023-01-01')  # Fecha ficticia
                    
                    def convert_time_str(time_str):
                        if ':' in time_str:
                            h, m = map(int, time_str.split(':')[:2])
                            return base_date + pd.Timedelta(hours=h, minutes=m)
                        return pd.NaT
                    
                    viajes_df['HORA_SALIDA'] = viajes_df['HORA_SALIDA'].apply(convert_time_str)
                    viajes_df['HORA_LLEGADA'] = viajes_df['HORA_LLEGADA'].apply(convert_time_str)
                # Si son minutos desde medianoche u otro formato numérico
                elif pd.api.types.is_numeric_dtype(viajes_df['HORA_SALIDA']):
                    print("Convirtiendo minutos a formato datetime...")
                    base_date = pd.Timestamp('2023-01-01')
                    viajes_df['HORA_SALIDA'] = viajes_df['HORA_SALIDA'].apply(
                        lambda x: base_date + pd.Timedelta(minutes=float(x))
                    )
                    viajes_df['HORA_LLEGADA'] = viajes_df['HORA_LLEGADA'].apply(
                        lambda x: base_date + pd.Timedelta(minutes=float(x))
                    )
            except Exception as e:
                print(f"Error al convertir formato de hora: {e}")
                print(f"Ejemplo de HORA_SALIDA: {viajes_df['HORA_SALIDA'].iloc[0]}")
                print(f"Ejemplo de HORA_LLEGADA: {viajes_df['HORA_LLEGADA'].iloc[0]}")
    
    # Depuración: Mostrar información del modelo
    print(f"Número de variables en el modelo: {len(modelo.getVars())}")
    variables_x = [v for v in modelo.getVars() if v.VarName.startswith('x_') and v.X > 0.5]
    print(f"Variables 'x' activadas: {len(variables_x)}")
    for v in variables_x[:5]:  # Mostrar algunos ejemplos
        print(f"  {v.VarName}: {v.X}")
    
    # Crear diccionario de solución
    solucion = {}
    for var in modelo.getVars():
        if var.VarName.startswith('x_'):
            # Extraer índices del nombre de la variable (x_u_i_j)
            partes = var.VarName.split('_')
            if len(partes) >= 4:  # Asegurarnos de que tiene el formato esperado
                _, u, i, j = partes
                # Solo considerar variables con valor cercano a 1 (decisiones activadas)
                if var.X > 0.5:
                    try:
                        solucion[(int(u), int(i), int(j))] = var.X
                    except ValueError:
                        print(f"Error al convertir índices en {var.VarName}")
                        continue
    
    print(f"Encontradas {len(solucion)} decisiones activadas")
    
    # Obtener las unidades que tienen rutas asignadas
    unidades = sorted(list(set(u for (u, _, _) in solucion.keys())))
    print(f"Unidades con rutas asignadas: {unidades}")
    
    # Usar el DataFrame de viajes proporcionado
    viajes = viajes_df.copy()
    if 'ID_VIAJE' not in viajes.columns:
        # Crear columna ID_VIAJE si no existe
        viajes['ID_VIAJE'] = list(range(1, len(viajes) + 1))
    
    rutas = []
    for unidad in unidades:
        print(f"\nProcesando unidad {unidad}")
        # Encontrar todos los viajes asignados a esta unidad
        viajes_unidad = [(i, j) for (u, i, j), valor in solucion.items() 
                        if u == unidad and valor > 0.5]
        
        print(f"  Viajes asignados: {len(viajes_unidad)}")
        if not viajes_unidad:
            continue
        
        print(f"  Ejemplos de viajes: {viajes_unidad[:3]}")
            
        # Ordenar los viajes por secuencia
        viajes_ordenados = []
        # Encontrar el primer viaje (el que no es destino de otro viaje)
        todos_destinos = [j for _, j in viajes_unidad]
        posibles_inicios = [i for i, _ in viajes_unidad if i not in todos_destinos]
        
        if posibles_inicios:
            try:
                primer_viaje = (posibles_inicios[0], next(j for i, j in viajes_unidad if i == posibles_inicios[0]))
                viajes_ordenados.append(primer_viaje)
                print(f"  Primer viaje encontrado: {primer_viaje}")
            except StopIteration:
                print(f"  Error al encontrar el siguiente viaje para {posibles_inicios[0]}")
                if viajes_unidad:
                    viajes_ordenados.append(viajes_unidad[0])
        else:
            # Si no hay un inicio claro, usar el primer viaje de la lista
            if viajes_unidad:
                viajes_ordenados.append(viajes_unidad[0])
                print(f"  Usando primer viaje disponible: {viajes_unidad[0]}")
        
        # Completar la secuencia de viajes
        try:
            while len(viajes_ordenados) < len(viajes_unidad):
                ultimo_viaje = viajes_ordenados[-1]
                siguiente_origen = ultimo_viaje[1]
                
                # Buscar el siguiente viaje en la secuencia
                siguiente_viaje = next((i, j) for i, j in viajes_unidad 
                                     if i == siguiente_origen and (i, j) not in viajes_ordenados)
                viajes_ordenados.append(siguiente_viaje)
        except StopIteration:
            print(f"  Advertencia: No se pudo completar la secuencia de viajes. Se procesarán los encontrados.")
        
        print(f"  Viajes ordenados: {len(viajes_ordenados)}")
        
        # Crear entradas para el DataFrame
        for idx, (i, j) in enumerate(viajes_ordenados):
            try:
                # Verificar que los IDs de viaje existen en el DataFrame de viajes
                if i not in viajes['ID_VIAJE'].values:
                    print(f"  Advertencia: ID_VIAJE {i} no encontrado en el DataFrame de viajes")
                    continue
                
                # Obtener información del viaje actual
                viaje_info = viajes[viajes['ID_VIAJE'] == i].iloc[0]
                
                # Obtener información del siguiente viaje (si no es el último)
                tiempo_anden = pd.NA
                if idx < len(viajes_ordenados) - 1:
                    siguiente_id = viajes_ordenados[idx+1][0]
                    if siguiente_id in viajes['ID_VIAJE'].values:
                        siguiente_viaje = viajes[viajes['ID_VIAJE'] == siguiente_id].iloc[0]
                        tiempo_anden = siguiente_viaje['HORA_SALIDA'] - viaje_info['HORA_LLEGADA']
                
                rutas.append({
                    'COD. OP.': unidad,
                    'ID_VIAJE': i,
                    'HORA_SALIDA': viaje_info['HORA_SALIDA'],
                    'HORA_LLEGADA': viaje_info['HORA_LLEGADA'],
                    'TIEMPO EN ANDÉN': tiempo_anden
                })
            except Exception as e:
                print(f"  Error al procesar viaje ({i}, {j}): {e}")
    
    result_df = pd.DataFrame(rutas)
    print(f"\nResultado final: {result_df.shape[0]} filas")
    if not result_df.empty:
        print(f"Columnas: {result_df.columns.tolist()}")
    
    return result_df

def visualize_routes(base: pd.DataFrame, 
                    valor_umbral: int = 100,
                    lineas_verticales: Optional[List[int]] = None,
                    max_unidades: int = 15,
                    figsize: tuple = (10, 8)) -> None:
    """
    Visualiza las rutas de los carros con sus tiempos de andén y viaje.
    
    Args:
        base (pd.DataFrame): DataFrame con los datos de las rutas
        valor_umbral (int): Valor umbral para cambiar el color del tiempo en andén
        lineas_verticales (List[int], optional): Lista de valores para líneas verticales
        max_unidades (int): Número máximo de unidades a mostrar
        figsize (tuple): Tamaño de la figura
    """
    # Verificar que el DataFrame no esté vacío
    if base.empty:
        print("El DataFrame está vacío. No hay rutas para visualizar.")
        return []
    
    print(f"Visualizando rutas - DataFrame shape: {base.shape}")
    print(f"Columnas disponibles: {base.columns.tolist()}")
    print(f"Primeras filas del DataFrame:\n{base.head()}")
    
    # Crear copia para no modificar el original
    base = base.copy()
    
    # Calcular tiempos de viaje
    if 'HORA_SALIDA' in base.columns and 'HORA_LLEGADA' in base.columns:
        # Asegurar que las columnas de tiempo estén en el formato correcto
        if not pd.api.types.is_datetime64_dtype(base['HORA_SALIDA']):
            try:
                print("Convirtiendo HORA_SALIDA a datetime...")
                base['HORA_SALIDA'] = pd.to_datetime(base['HORA_SALIDA'])
                print("Conversión exitosa de HORA_SALIDA")
            except Exception as e:
                print(f"Error al convertir HORA_SALIDA a datetime: {e}")
                print(f"Ejemplo de valor: {base['HORA_SALIDA'].iloc[0]}")
                return []
                
        if not pd.api.types.is_datetime64_dtype(base['HORA_LLEGADA']):
            try:
                print("Convirtiendo HORA_LLEGADA a datetime...")
                base['HORA_LLEGADA'] = pd.to_datetime(base['HORA_LLEGADA'])
                print("Conversión exitosa de HORA_LLEGADA")
            except Exception as e:
                print(f"Error al convertir HORA_LLEGADA a datetime: {e}")
                print(f"Ejemplo de valor: {base['HORA_LLEGADA'].iloc[0]}")
                return []
        
        print("Calculando TIEMPO_VIAJE...")
        # Calcular tiempo de viaje en minutos
        base['TIEMPO_VIAJE'] = (base['HORA_LLEGADA'] - base['HORA_SALIDA']).dt.total_seconds() / 60
        print(f"Estadísticas de TIEMPO_VIAJE: Min={base['TIEMPO_VIAJE'].min()}, Max={base['TIEMPO_VIAJE'].max()}, Media={base['TIEMPO_VIAJE'].mean()}")
    
    # Calcular tiempos en andén en minutos si no existe la columna ANDEN_MINUTOS
    if 'ANDEN_MINUTOS' not in base.columns and 'TIEMPO EN ANDÉN' in base.columns:
        print("Calculando ANDEN_MINUTOS desde 'TIEMPO EN ANDÉN'...")
        
        def convertir_a_minutos(tiempo):
            if pd.isna(tiempo):
                return pd.NA
            if isinstance(tiempo, pd.Timedelta):
                return tiempo.total_seconds() / 60
            elif isinstance(tiempo, str):
                try:
                    # Intentar parsear formato hh:mm
                    partes = tiempo.split(':')
                    return int(partes[0]) * 60 + int(partes[1])
                except:
                    return pd.NA
            return tiempo  # Devolver el valor tal cual si no se puede convertir
            
        base['ANDEN_MINUTOS'] = base['TIEMPO EN ANDÉN'].apply(convertir_a_minutos)
        print(f"Porcentaje de valores no-NA en ANDEN_MINUTOS: {base['ANDEN_MINUTOS'].notna().mean()*100:.1f}%")
    
    # Obtener las unidades únicas
    unidades = base['COD. OP.'].unique()
    print(f"Unidades encontradas: {unidades}")
    
    # Limitar el número de unidades a visualizar
    if len(unidades) > max_unidades:
        unidades = unidades[:max_unidades]
        print(f"Visualizando solo las primeras {max_unidades} unidades.")
    
    # Crear subgráficos
    fig, axs = plt.subplots(len(unidades), 1, figsize=figsize, sharex=True)
    
    # Manejar caso de una sola unidad
    if len(unidades) == 1:
        axs = [axs]
    
    # Valores por defecto para líneas verticales
    if lineas_verticales is None:
        lineas_verticales = [225, 255, 480, 655, 685]
    
    resultados = []
    for i, unidad in enumerate(unidades):
        base_unidad = base[base['COD. OP.'] == unidad].sort_values('HORA_SALIDA')
        print(f"Procesando unidad {unidad} - {len(base_unidad)} viajes")
        
        Type = []
        Time = []
        Colors = []
        
        for idx, row in base_unidad.iterrows():
            # Añadir tiempo de viaje
            if 'TIEMPO_VIAJE' in base_unidad.columns:
                if not pd.isna(row['TIEMPO_VIAJE']):
                    Type.append('Viaje')
                    Time.append(row['TIEMPO_VIAJE'])
                    Colors.append('lightgreen')
            
            # Añadir tiempo en andén si no es el último viaje y no es NA
            if 'ANDEN_MINUTOS' in base_unidad.columns and not pd.isna(row['ANDEN_MINUTOS']):
                Type.append('Andén')
                Time.append(row['ANDEN_MINUTOS'])
                Colors.append('orange' if row['ANDEN_MINUTOS'] <= valor_umbral else 'skyblue')
        
        data = pd.DataFrame({
            "Type": Type,
            "Time": Time,
            "Colors": Colors
        })
        
        print(f"  Datos para visualización: {len(data)} elementos")
        resultados.append(data)
        
        if data.empty:
            print(f"  ¡Advertencia! No hay datos para visualizar para la unidad {unidad}")
            continue
        
        # Dibujar barras
        left = 0
        bar_height = 0.3
        for _, row in data.iterrows():
            axs[i].barh(y=0, width=row['Time'], left=left, color=row['Colors'], height=bar_height)
            left += row['Time']
        
        # Añadir texto con el tiempo total
        total_time = sum(data['Time'])
        axs[i].text(left + 0.5, 0, f'{total_time:.2f} min', va='center', fontsize=9)
        
        # Configurar ejes
        axs[i].set_yticks([])
        axs[i].set_title(f'Unidad {unidad}', fontsize=10)
        
        # Añadir líneas verticales
        for x_value in lineas_verticales:
            axs[i].axvline(x=x_value, color='red', linestyle='--', linewidth=1)
    
    # Verificar si algún gráfico se dibujó correctamente
    if all(d.empty for d in resultados):
        print("No hay datos para visualizar en ninguna unidad.")
        plt.close(fig)
        return resultados
    
    # Crear leyenda
    import matplotlib.patches as mpatches
    viaje_patch = mpatches.Patch(color='lightgreen', label='Tiempo de viaje')
    anden_normal_patch = mpatches.Patch(color='orange', label=f'Tiempo en andén ≤ {valor_umbral} min')
    anden_largo_patch = mpatches.Patch(color='skyblue', label=f'Tiempo en andén > {valor_umbral} min')
    
    fig.legend(handles=[viaje_patch, anden_normal_patch, anden_largo_patch], 
              loc='lower center', ncol=3, bbox_to_anchor=(0.5, 0))
    
    # Etiquetas comunes
    fig.text(0.5, 0.04, 'Tiempo (minutos)', ha='center')
    fig.suptitle('Rutas de las unidades', fontsize=16)
    
    plt.tight_layout(rect=[0, 0.07, 1, 0.95])
    plt.show()
    
    return resultados, 0.95
    plt.show()
    
    return resultados