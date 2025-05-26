#include "gurobi_c++.h"
#include <iostream>
#include <vector>
#include <map>
#include <string>

using namespace std;

int main() {
    try {
        // Crear entorno y modelo
        GRBEnv env = GRBEnv(true);
        env.set("LogFile", "flujo.log");
        env.start();
        GRBModel model = GRBModel(env);

        // Datos del problema
        vector<string> nodos = {"A", "B", "C", "D"};
        vector<pair<string, string>> arcos = {{"A", "B"}, {"A", "C"}, {"B", "D"}, {"C", "D"}};

        map<pair<string, string>, int> capacidades = {
            {{"A", "B"}, 15}, {{"A", "C"}, 20}, {{"B", "D"}, 10}, {{"C", "D"}, 20}
        };

        map<pair<string, string>, int> costos = {
            {{"A", "B"}, 4}, {{"A", "C"}, 2}, {{"B", "D"}, 1}, {{"C", "D"}, 3}
        };

        map<string, int> demanda = {
            {"A", -25}, {"B", 0}, {"C", 0}, {"D", 25}
        };

        // Variables de flujo (enteras y >= 0)
        map<pair<string, string>, GRBVar> flujo;
        for (auto& arco : arcos) {
            flujo[arco] = model.addVar(0.0, capacidades[arco], 0.0, GRB_INTEGER,
                                       "flujo_" + arco.first + "_" + arco.second);
        }

        // Función objetivo: minimizar el costo total del flujo
        GRBLinExpr obj = 0;
        for (auto& arco : arcos) {
            obj += costos[arco] * flujo[arco];
        }
        model.setObjective(obj, GRB_MINIMIZE);

        // Restricciones de conservación de flujo por nodo
        for (const string& nodo : nodos) {
            GRBLinExpr balance = 0;

            // Flujo que entra al nodo
            for (auto& arco : arcos) {
                if (arco.second == nodo)
                    balance += flujo[arco];
            }

            // Flujo que sale del nodo
            for (auto& arco : arcos) {
                if (arco.first == nodo)
                    balance -= flujo[arco];
            }

            model.addConstr(balance == demanda[nodo], "flujo_" + nodo);
        }

        // Resolver el modelo
        model.optimize();

        // Mostrar resultados
        if (model.get(GRB_IntAttr_Status) == GRB_OPTIMAL) {
            cout << "Solución óptima encontrada:\n";
            for (auto& arco : arcos) {
                cout << "Flujo de " << arco.first << " a " << arco.second << ": "
                     << flujo[arco].get(GRB_DoubleAttr_X) << endl;
            }
            cout << "Costo total: " << model.get(GRB_DoubleAttr_ObjVal) << endl;
        } else {
            cout << "No se encontró una solución óptima.\n";
        }

    } catch (GRBException e) {
        cerr << "Error de Gurobi: " << e.getMessage() << endl;
    } catch (...) {
        cerr << "Error desconocido.\n";
    }

    return 0;
}
