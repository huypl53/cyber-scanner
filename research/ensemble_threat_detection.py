# %% [markdown]
# # Threat detection Model- Ensembling LSTM and ANN

# %% [markdown]
# ### Loading Libraries

# %%
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pandas.api.types import is_numeric_dtype
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, roc_curve, auc, roc_auc_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE
import itertools
import warnings
warnings.filterwarnings('ignore')
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization, ReLU, LSTM
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import BinaryCrossentropy
from google.colab import drive
import os
import joblib

# %%
drive.mount('/content/drive')

# %% [markdown]
# ### Loading Dataset

# %%
# Load the dataset
ds = pd.read_csv("/content/dataset.csv")

# %%
ds.info()

# %%
ds.shape

# %%
ds.head()

# %%
ds.describe()

# %%
ds.describe(include='object')

# %% [markdown]
# ### Exploratory Data Analysis

# %%
# Visualize the class distribution
ds['class'].value_counts()

# %%
sns.countplot(x=ds['class'])
plt.show()

# %%
# Visualize protocol types
ds['protocol_type'].value_counts()

# %%
sns.countplot(x=ds['protocol_type'])
plt.show()

# %%
# Heatmap for correlation
sns.heatmap(ds.corr(numeric_only=True))
plt.show()

# %% [markdown]
# ### Data Preprocessing

# %%
ds.isnull().sum()

# %%
ds.duplicated().sum()

# %%
# Encode categorical features
label_encoder = LabelEncoder()
def le(df):
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = label_encoder.fit_transform(df[col])

# %%
le(ds)
(ds.head())

# %%
ds.drop(['num_outbound_cmds'], axis=1, inplace=True)

# %%
# Feature Selection
X = ds.drop(['class'], axis=1)
y = ds['class']
rfc = RandomForestClassifier()
rfe = RFE(rfc, n_features_to_select=10)
rfe = rfe.fit(X, y)
feature_map = [(i, v) for i, v in itertools.zip_longest(rfe.get_support(), X.columns)]
selected_features = [v for i, v in feature_map if i]
top_features = pd.DataFrame({'Features': selected_features})
top_features.index = top_features.index + 1

# %%
print(top_features)

# %%
X = X[selected_features]
scale = StandardScaler()
X = scale.fit_transform(X)

# %%

# ANN train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.25, random_state=42)

# LSTM train-test split
X_trainL, X_testL, y_trainL, y_testL = train_test_split(X, y, test_size=0.2, random_state=42)
X_trainL, X_valL, y_trainL, y_valL = train_test_split(X_trainL, y_trainL, test_size=0.25, random_state=42)

# %% [markdown]
# ### ANN- Binary Classificaton

# %%
# ANN model
model_ann = Sequential()
model_ann.add(Dense(128, input_dim=X_train.shape[1]))
model_ann.add(ReLU())
model_ann.add(BatchNormalization())
model_ann.add(Dense(128))
model_ann.add(ReLU())
model_ann.add(BatchNormalization())
model_ann.add(Dropout(0.2))
model_ann.add(Dense(64))
model_ann.add(ReLU())
model_ann.add(BatchNormalization())
model_ann.add(Dropout(0.2))
model_ann.add(Dense(32))
model_ann.add(ReLU())
model_ann.add(BatchNormalization())
model_ann.add(Dropout(0.2))
model_ann.add(Dense(1, activation='sigmoid'))

# %%
#training and compilation
model_ann.compile(optimizer=Adam(learning_rate=0.001), loss=BinaryCrossentropy(), metrics=['accuracy'])
history_ann = model_ann.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_val, y_val))

# %%
#classification report and
y_pred_ann = model_ann.predict(X_test)
y_pred_ann = (y_pred_ann > 0.5)
accuracy_ann = accuracy_score(y_test, y_pred_ann)
print("Test Accuracy of ANN Model:", accuracy_ann * 100)
print(classification_report(y_test, y_pred_ann))
cm_ann = confusion_matrix(y_test, y_pred_ann)
sns.heatmap(cm_ann, annot=True, fmt="d")
plt.show()

# %%

# Calculate ROC and AUC
fpr_ann, tpr_ann, thresholds_ann = roc_curve(y_test, y_pred_ann)
auc_ann = roc_auc_score(y_test, y_pred_ann)

# Plot ROC and AUC
plt.figure()
plt.plot(fpr_ann, tpr_ann, label="ANN (AUC = %0.2f)" % auc_ann)
plt.plot([0, 1], [0, 1], "k--")
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC and AUC for ANN Model")
plt.legend(loc="lower right")
plt.show()


# %%
# Save the ANN model
ann_model_path = '/content/drive/My Drive/MyModels/ANN_model.h5'
os.makedirs(os.path.dirname(ann_model_path), exist_ok=True)
model_ann.save(ann_model_path)
print("ANN model saved successfully.")

# %% [markdown]
# ### LSTM

# %%
# Reshape the input data for LSTM
X_trainL = np.reshape(X_trainL, (X_trainL.shape[0], X_trainL.shape[1], 1))
X_valL = np.reshape(X_valL, (X_valL.shape[0], X_valL.shape[1], 1))
X_testL = np.reshape(X_testL, (X_testL.shape[0], X_testL.shape[1], 1))

# %%
# LSTM model
model_lstm = Sequential([
    LSTM(units=256, return_sequences=True, input_shape=(X_trainL.shape[1], X_trainL.shape[2])),
    Dropout(0.2),
    LSTM(units=128, return_sequences=True),
    Dropout(0.2),
    LSTM(units=64),
    Dropout(0.2),
    Dense(1, activation='sigmoid')
])

# %%
#training and compilation
model_lstm.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
history_lstm=model_lstm.fit(X_trainL, y_trainL, epochs= 10, batch_size=128, validation_data=(X_valL, y_valL))

# %%
#Classification Report and Confusion  Matrix
y_pred_lstm=model_lstm.predict(X_testL)
y_pred_lstm=(y_pred_lstm> 0.5)
accuracy_lstm=accuracy_score(y_testL, y_pred_lstm)
print("Test Accuracy of LSTM Model:", accuracy_lstm * 100)
print(classification_report(y_testL, y_pred_lstm))
cm_lstm= confusion_matrix(y_testL, y_pred_lstm)
sns.heatmap(cm_lstm, annot= True, fmt="d")
plt.show()

# %%
# Calculate ROC and AUC for LSTM model
fpr_lstm, tpr_lstm, thresholds_lstm = roc_curve(y_testL, y_pred_lstm)
auc_lstm = roc_auc_score(y_testL, y_pred_lstm)

# Plot ROC and AUC for LSTM model
plt.figure()
plt.plot(fpr_lstm, tpr_lstm, label="LSTM (AUC = %0.2f)" % auc_lstm)
plt.plot([0, 1], [0, 1], "k--")
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC and AUC for LSTM Model")
plt.legend(loc="lower right")
plt.show()


# %%
# Save the LSTM model
lstm_model_path = '/content/drive/My Drive/MyModels/LSTM_model.h5'
os.makedirs(os.path.dirname(lstm_model_path), exist_ok=True)
model_lstm.save(lstm_model_path)
print("LSTM model saved successfully.")

# %% [markdown]
# ### Ensemble

# %%
class EnsembleModel:
    def __init__(self, ann_model_path, lstm_model_path):
        self.model_ann = load_model(ann_model_path)
        self.model_lstm = load_model(lstm_model_path)

    def predict(self, X):
        X_lstm = np.reshape(X, (X.shape[0], X.shape[1], 1))
        y_pred_prob_ann = self.model_ann.predict(X)
        y_pred_prob_lstm = self.model_lstm.predict(X_lstm)
        y_pred_prob_ensemble = (y_pred_prob_ann + y_pred_prob_lstm) / 2
        y_pred_ensemble = (y_pred_prob_ensemble > 0.5).astype(int)
        return y_pred_ensemble

# %%
# Save the ensemble model class
ensemble_model = EnsembleModel(ann_model_path, lstm_model_path)
ensemble_model_path = '/content/drive/My Drive/MyModels/ensemble_model.pkl'
os.makedirs(os.path.dirname(ensemble_model_path), exist_ok=True)
with open(ensemble_model_path, 'wb') as f:
    joblib.dump(ensemble_model, f)

# %%
# Train the ensemble model for 10 epochs
ensemble_model.model_ann.fit(X_train, y_train, epochs=5, batch_size=32, validation_data=(X_val, y_val))
ensemble_model.model_lstm.fit(X_trainL, y_trainL, epochs=5, batch_size=128, validation_data=(X_valL, y_valL))

# %%
# Predict on the test set
y_pred_ensemble = ensemble_model.predict(X_test)

# Calculate the test accuracy
accuracy_ensemble = accuracy_score(y_test, y_pred_ensemble)
print("Test Accuracy of Ensemble Model:", accuracy_ensemble * 100)

# Print the classification report
print(classification_report(y_test, y_pred_ensemble))

# Plot the confusion matrix
cm_ensemble = confusion_matrix(y_test, y_pred_ensemble)
sns.heatmap(cm_ensemble, annot=True, fmt="d")
plt.show()


# %%
#AUC- ROC Curve
# Plot the ROC and AUC for the ensemble model
plt.figure()
plt.plot(fpr_ann, tpr_ann, label="ANN (AUC = %0.2f)" % auc_ann, color='blue')
plt.plot(fpr_lstm, tpr_lstm, label="LSTM (AUC = %0.2f)" % auc_lstm, color='green')
plt.plot(fpr_ensemble, tpr_ensemble, label="Ensemble (AUC = %0.2f)" % auc_ensemble, color='purple')
plt.plot([0, 1], [0, 1], "k--")
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC and AUC for Ensemble Model")
plt.legend(loc="lower right")
plt.show()


# %%



