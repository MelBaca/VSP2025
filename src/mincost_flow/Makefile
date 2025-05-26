# Nombre del ejecutable
TARGET = mincost_flow

# Archivos fuente
SRC = mincost_flow.cpp

# Compilador
CXX = g++

# Paths (relativos a GUROBI_HOME)
INCLUDES = -I$(GUROBI_HOME)/include
LIBS = -L$(GUROBI_HOME)/lib -lgurobi_c++ -lgurobi110

# Flags de compilación
CXXFLAGS = -O2 -std=c++11 $(INCLUDES)

# Regla por defecto
all: $(TARGET)

# Cómo construir el ejecutable
$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC) $(LIBS)

# Limpiar archivos generados
clean:
	rm -f $(TARGET)
