import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from scipy.stats import kstest,normaltest,shapiro
warnings.filterwarnings('ignore')
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,classification_report


class DataFrameAnalyzer:
    def __init__(self, dataframe: pd.DataFrame):
        """
        Inicializa la clase con un DataFrame
        """
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("El argumento debe ser un DataFrame de pandas.")
        self.df = dataframe

    def resumen(self) -> pd.DataFrame:
        """
        Retorna un resumen detallado del dataset en formato DataFrame:
        - Tipo de Dato
        - Cardinalidad
        - % Cardinalidad
        - Valores Faltantes
        - % Valores Faltantes
        - Categoría
        """
        total_rows = len(self.df)
        summary = []

        for col in self.df.columns:
            # Tipo de dato
            data_type = self.df[col].dtype

            # Cardinalidad y % Cardinalidad
            cardinality = self.df[col].nunique()
            cardinality_pct = (cardinality / total_rows) * 100

            # Valores faltantes y % Valores faltantes
            missing = self.df[col].isnull().sum()
            missing_pct = (missing / total_rows) * 100

            # Determinar la categoría de la columna
            if pd.api.types.is_numeric_dtype(self.df[col]):
                if cardinality == 2:
                    category = "Binaria"
                elif np.issubdtype(self.df[col].dtype, np.integer):
                    category = "Numérica Discreta"
                else:
                    category = "Numérica Continua"
            elif pd.api.types.is_object_dtype(self.df[col]) or pd.api.types.is_categorical_dtype(self.df[col]):
                if cardinality == 2:
                    category = "Binaria"
                else:
                    category = "Categórica Nominal"
            else:
                category = "Otro"

            # Clasificar "rowid" o índices numéricos
            if "id" in col.lower() or col.lower() == "rowid":
                category = "Índice Numérico"

            # Añadir fila al resumen
            summary.append({
                "Columna": col,
                "Tipo de Dato": data_type,
                "Cardinalidad": cardinality,
                "% Cardinalidad": round(cardinality_pct, 2),
                "Valores Faltantes": missing,
                "% Valores Faltantes": round(missing_pct, 2),
                "Categoría": category
            })

        # Crear DataFrame resumen
        summary_df = pd.DataFrame(summary)
        return summary_df

    def describe_numeric(self) -> pd.DataFrame:
        """
        Análisis estadístico detallado de variables numéricas:
        - Media, mediana, moda
        - Desviación estándar
        - Cuartiles
        - Asimetría y curtosis
        """
        numeric_df = self.df.select_dtypes(include=['number'])  # Filtrar solo variables numéricas
        numeric_df = numeric_df[[col for col in numeric_df.columns if "id" not in col.lower() and col.lower() != "rowid"]] # Excluyendo variables con 'ID'
        
        # Calcular estadísticas
        stats = numeric_df.describe().T
        stats['mean'] = numeric_df.mean()
        stats['median'] = numeric_df.median()
        stats['mode'] = numeric_df.mode().iloc[0]
        stats['std_dev'] = numeric_df.std()
        stats['skewness'] = numeric_df.skew()
        stats['kurtosis'] = numeric_df.kurt()
        
        return stats[['count', 'mean', 'median', 'mode', 'std_dev', 'min', '25%', '50%', '75%', 'max', 'skewness', 'kurtosis']]

    def describe_categorical(self) -> pd.DataFrame:
        """
        Análisis de variables categóricas:
        - Frecuencias
        - Proporciones
        - Valores únicos
        """
        categorical_df = self.df.select_dtypes(include=['object', 'category'])  # Filtrar variables categóricas
        
        # Calcular estadísticas
        stats = {
            "unique_values": categorical_df.nunique(),
            "most_frequent": categorical_df.mode().iloc[0],
            "frequency": categorical_df.apply(lambda x: x.value_counts().iloc[0]),
            "proportion": round((categorical_df.apply(lambda x: x.value_counts(normalize=True).iloc[0])*100),2)
        }
        
        return pd.DataFrame(stats)
    
    def plot_numeric(self):
        """
        Genera histogramas y boxplots para todas las variables numéricas.
        """
        numeric_df = self.df.select_dtypes(include=['number'])
        for col in numeric_df.columns:
            plt.figure(figsize=(14, 6))
            
            # Histograma
            plt.subplot(1, 2, 1)
            sns.histplot(numeric_df[col], kde=True, bins=20, color='blue')
            plt.title(f"Distribución de {col}")
            plt.xlabel(col)
            plt.ylabel("Frecuencia")
            
            # Boxplot
            plt.subplot(1, 2, 2)
            sns.boxplot(x=numeric_df[col], color='green')
            plt.title(f"Boxplot de {col}")
            plt.xlabel(col)
            
            plt.tight_layout()
            plt.show()

    def plot_categorical(self, max_cats=10):
        """
        Genera gráficos para variables categóricas, manejando un gran número de categorías.

        Args:
            max_cats (int): Número máximo de categorías a mostrar en el gráfico.
        """
        categorical_df = self.df.select_dtypes(include=['object', 'category'])
        for col in categorical_df.columns:
            num_cats = categorical_df[col].nunique()

            plt.figure(figsize=(14, min(num_cats * 0.5, 12))) #Ajusta el tamaño del grafico segun la cantidad de categorias hasta un maximo

            # Gráfico de barras (horizontal)
            plt.subplot(1, 2, 1)
            counts = categorical_df[col].value_counts()
            
            if num_cats > max_cats:
                counts = counts[:max_cats]
                plt.title(f"Frecuencia de {col} (Top {max_cats})")
            else:
                plt.title(f"Frecuencia de {col}")
            
            sns.barplot(x=counts.values, y=counts.index, palette="viridis")
            plt.xlabel("Frecuencia")
            plt.ylabel(col)

            # Pie chart (solo para un número manejable de categorías)
            if num_cats <= max_cats: #Solo muestra el pie chart si la cantidad de categorias es menor o igual al maximo
                plt.subplot(1, 2, 2)
                counts.plot.pie(autopct='%1.1f%%', startangle=90, cmap="viridis", textprops={'fontsize': 10}) #Ajusta el tamaño de la fuente del pie chart
                plt.title(f"Proporción de {col}")
                plt.ylabel("")
            else:
                plt.subplot(1,2,2)
                plt.text(0.5, 0.5, f"Demasiadas categorías ({num_cats}) para mostrar en un gráfico circular.", ha='center', va='center', fontsize=12) #Mensaje alternativo
                plt.axis('off')

            plt.tight_layout()
            plt.show()

    def test_Ksmirnov(self) -> pd.DataFrame:
            """
            Realiza el test de Shapiro-Wilk a todas las variables numéricas de un DataFrame.

            Args:
                df: El DataFrame de pandas.

            Returns:
                Un diccionario con los resultados del test para cada variable numérica.

            """
            lista = []
            variables_numericas =self.df.select_dtypes(include=['number'])
            
            for columna in variables_numericas.columns:
                stat, p = kstest(self.df[columna],'norm')
                resultado = (f"Columna: {columna:<20} | Estadístico: {stat:.6f} | P-Valor: {p}")
                lista.append(resultado)
                
            return lista

    def test_normalidad(self):

            lista = []
            variables_numericas =self.df.select_dtypes(include=['number'])
                
            for columna in variables_numericas.columns:
                stat, p = normaltest(self.df[columna])
                resultado = (f"Columna: {columna:<20} | Estadístico: {stat:.6f} | P-Valor: {p}")
                lista.append(resultado)
                    
            return lista

    def test_shapiro(self):
            lista = []
            variables_numericas =self.df.select_dtypes(include=['number'])
                
            for columna in variables_numericas.columns:
                stat, p = shapiro(self.df[columna])
                resultado = (f"Columna: {columna:<20} | Estadístico: {stat:.6f} | P-Valor: {p}")
                lista.append(resultado)
                        
            return lista

    def classification_ML(self,x,y):
    
            k=KNeighborsClassifier()
            svc=SVC()
            d=DecisionTreeClassifier()
            log=LogisticRegression()
            gbc=GradientBoostingClassifier()
            rf=RandomForestClassifier()
            xgb = XGBClassifier()
            ab=AdaBoostClassifier()
            
            algos=[k,svc,d,log,gbc,rf,xgb,ab]
            algos_name=['KNeigbors','SVC','DecisionTree','LogisticRegr','GradientBoosting','RandomForest','XGBClassifier','AdaBoost']
            
            accuracy = []
            precision = []
            recall = []
            f1 = []
            class_report = []
        
            result=pd.DataFrame(columns=['AccuracyScore','PrecisionScore','RecallScore','f1_Score'],index=algos_name)

            x_train,x_test,y_train,y_test=train_test_split(x,y,random_state=42)

            for i in algos:
                
                predict=i.fit(x_train,y_train).predict(x_test)

                class_report.append(classification_report(y_test,predict))
                accuracy.append(accuracy_score(y_test,predict))
                precision.append(precision_score(y_test,predict,average='weighted'))
                recall.append(recall_score(y_test,predict,average='weighted'))
                f1.append(f1_score(y_test,predict,average='weighted'))
            
            result.AccuracyScore=accuracy
            result.PrecisionScore=precision
            result.RecallScore=recall
            result.f1_Score=f1
            
            return result.sort_values('f1_Score',ascending=False), print(class_report)
    

    def regression_ML(self, x, y):

            models = [
                KNeighborsRegressor(),
                SVR(),
                DecisionTreeRegressor(),
                LinearRegression(),
                GradientBoostingRegressor(),
                RandomForestRegressor(),
                AdaBoostRegressor(),
                XGBRegressor()
            ]

            model_names = [
                'KNeighbors',
                'SVR',
                'DecisionTree',
                'LinearRegression',
                'GradientBoosting',
                'RandomForest',
                'AdaBoost',
                'XGBRegressor'
            ]

            mae_list = []
            mse_list = []
            rmse_list = []
            r2_list = []

            results = pd.DataFrame(columns=['MAE', 'MSE', 'RMSE', 'R2'], index=model_names)

            x_train, x_test, y_train, y_test = train_test_split(x, y, random_state=42)

            for model in models:
                y_pred = model.fit(x_train, y_train).predict(x_test)

                mae_list.append(mean_absolute_error(y_test, y_pred))
                mse_list.append(mean_squared_error(y_test, y_pred))
                rmse_list.append(np.sqrt(mean_squared_error(y_test, y_pred)))
                r2_list.append(r2_score(y_test, y_pred))

            results['MAE'] = mae_list
            results['MSE'] = mse_list
            results['RMSE'] = rmse_list
            results['R2'] = r2_list

            return results.sort_values('R2', ascending=False)
