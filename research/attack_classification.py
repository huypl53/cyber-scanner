# %% [markdown]
# # Attack Classification

# %%
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Conv1D, MaxPooling1D, LSTM
from itertools import combinations
import seaborn as sns
import matplotlib.pyplot as plt
from google.colab import drive
from tensorflow.keras.models import save_model
from sklearn.preprocessing import RobustScaler
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
import joblib
# Mount Google Drive
drive.mount('/content/drive')

# %%
df1=pd.read_csv("/content/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv")
df2=pd.read_csv("/content/Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv")
df3=pd.read_csv("/content/Friday-WorkingHours-Morning.pcap_ISCX.csv")
df4=pd.read_csv("/content/Monday-WorkingHours.pcap_ISCX.csv")
df5=pd.read_csv("/content/Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv")
df6=pd.read_csv("/content/Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv")
df7=pd.read_csv("/content/Tuesday-WorkingHours.pcap_ISCX.csv")
df8=pd.read_csv("/content/Wednesday-workingHours.pcap_ISCX.csv")

df = pd.concat([df1,df2,df3,df4,df5,df6,df7,df8])
df.reset_index(drop=True, inplace=True)
print("Shape of combined DataFrame:", df.shape)

# %%
df.head()

# %%
df.isnull().sum()

# %%
df.describe().T

# %%
df.info()

# %%
df.duplicated().sum()

# %%
df =  df.drop_duplicates(keep="first")
df.dropna(inplace=True)
df.shape

# %%
print(df.columns)

# %%
prediction_counts = df[' Label'].value_counts()
print(prediction_counts)

# %%
integer = []
f = []
for i in df.columns[:-1]:
    if df[i].dtype == "int64": integer.append(i)
    else : f.append(i)

df[integer] = df[integer].astype("int32")
df[f] = df[f].astype("float32")

# %%
df = df.replace([np.inf, -np.inf], np.nan).dropna()

# %%
import seaborn as sns
import matplotlib.pyplot as plt

prediction_counts= df[' Label'].value_counts()

plt.figure(figsize=(10, 6))
sns.barplot(x=prediction_counts.index, y=prediction_counts.values)
plt.title('Distribution of Labels')
plt.xlabel('Label')
plt.ylabel('Count')
plt.xticks(rotation=60)
plt.show()

# %%
objList = df.select_dtypes(include = "object").columns
print (objList)

# %%
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()

for feat in objList:
    df[feat] = le.fit_transform(df[feat].astype(str))

print (df.info())

# %%
def correlation(dataset, threshold):
    col_corr = set()
    corr_matrix =df.corr()
    for i in range(len(corr_matrix.columns)):
        for j in range(i):
            if abs(corr_matrix.iloc[i, j]) > threshold:
              colname = corr_matrix.columns[i]
              col_corr.add(colname)
    return col_corr

corr_features = correlation(df, 0.85)
corr_features

# %%
df.drop(corr_features,axis=1,inplace=True)

# %%
X= df.drop([' Label'],axis=1)
y = df[' Label']

# %%
unique_labels = y.unique()
print(unique_labels)

# %%
scaler = RobustScaler()
X_scaled = scaler.fit_transform(X)

# %%
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, shuffle=True)
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.25, random_state=42, shuffle=True)

# %%
df.columns

# %% [markdown]
# ###Model

# %%
model = DecisionTreeClassifier(criterion='entropy', max_depth=10)
model.fit(X_train, y_train)


# %%
y_pred = model.predict(X_test)

# %%
# Calculate training and testing accuracy
training_accuracy = accuracy_score(y_train, model.predict(X_train))
testing_accuracy = accuracy_score(y_test, y_pred)

# Print the results
print("Training accuracy:", training_accuracy)
print("Testing accuracy:", testing_accuracy)


# %%
# Classification report
print(classification_report(y_test, y_pred))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)

# Plot confusion matrix
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False)
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.title("Confusion Matrix")
plt.show()


# %%
le.inverse_transform(y_pred)
print(classification_report(le.inverse_transform(y_test), le.inverse_transform(y_pred)))


# %%
# Specify the directory path where you want to save the model
model_dir = '/content/drive/My Drive/MyModels/'
model_path = model_dir + 'decision_tree_model.joblib'

# Save the model
joblib.dump(model, model_path)

print(f"Model saved to {model_path}")



