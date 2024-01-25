# -*- coding: utf-8 -*-
"""CNN

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1pLvnor0bruwUTknnDru6eXQvc0T6GCxt

<h3 style="text-align: center;"><b>Полносвязные и свёрточные нейронные сети</b></h3>

В этом ноутбуке мы рассмотрим простейшие нейронные сети с помощью библиотеки Pytorch. Делать мы это будем на нескольких датасетах.
"""

import numpy as np

import seaborn as sns
from matplotlib import pyplot as plt

from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split

import torch
from torch import nn
from torch.nn import functional as F

from torch.utils.data import TensorDataset, DataLoader

import warnings
warnings.filterwarnings("ignore")

sns.set(style="darkgrid", font_scale=1.4)

"""# Часть 1. Датасет moons
Сгенерируем датасет и посмотрим на него.
"""

X, y = make_moons(n_samples=10000, random_state=42, noise=0.1)

plt.figure(figsize=(16, 10))
plt.title("Dataset")
plt.scatter(X[:, 0], X[:, 1], c=y, cmap="viridis")
plt.show()

"""Сделаем train/test split"""

X_train, X_val, y_train, y_val = train_test_split(X, y, random_state=42)

"""### Загрузка данных
В PyTorch загрузка данных как правило происходит налету. Для этого используются две сущности `Dataset` и `DataLoader`.

1.   `Dataset` загружает каждый объект по отдельности.

2.   `DataLoader` группирует объекты из `Dataset` в батчи.



### Задание. Создайте тензоры с обучающими и тестовыми данными

Далее нам необходимо создать тензоры - переведем массивы numpy в тензоры с типом `torch.float32`.
"""

X_train_t =  torch.FloatTensor(X_train)
y_train_t =  torch.FloatTensor(y_train)
X_val_t = torch.FloatTensor(X_val)
y_val_t =  torch.FloatTensor(y_val)

"""Создаем `Dataset` и `DataLoader`."""

train_dataset = TensorDataset(X_train_t, y_train_t)
val_dataset = TensorDataset(X_val_t, y_val_t)
train_dataloader = DataLoader(train_dataset, batch_size=128)
val_dataloader = DataLoader(val_dataset, batch_size=128)

"""## Logistic regression is my profession

Давайте вспоним, что происходит в логистической регрессии. На входе у нас есть матрица объект-признак X и столбец-вектор $y$ – метки из $\{0, 1\}$ для каждого объекта. Мы хотим найти такую матрицу весов $W$ и смещение $b$ (bias), что наша модель $XW + b$ будет каким-то образом предсказывать класс объекта. Как видно на выходе наша модель может выдавать число в интервале от $(-\infty;\infty)$. Этот выход как правило называют "логитами" (logits). Нам необходимо перевести его на интервал от $[0;1]$ для того, чтобы он выдавал нам вероятность принадлежности объекта к кассу один, также лучше, чтобы эта функция была монотонной, быстро считалась, имела производную и на $-\infty$ имела значение $0$, а на $+\infty$ имела значение $1$. Такой класс функций называется сигмоидыю. Чаще всего в качестве сигмоида берут
$$
\sigma(x) = \frac{1}{1 + e^{-x}}.
$$

### Задание. Реализация логистической регрессии

Напишем модуль на PyTorch реализующий $logits = XW + b$, где $W$ и $b$ – параметры (`nn.Parameter`) модели. Иначе говоря, здесь мы реализуем своими руками модуль `nn.Linear` (в этом пункте его использование запрещено). Инициализируем веса нормальным распределением (`torch.randn`).
"""

from torch.cuda.random import Tensor
class LinearRegression(nn.Module):
    def __init__(self, in_features: int, out_features: int, bias: bool = True):
        super().__init__()
        self.weights = nn.Parameter(torch.randn(out_features, in_features))
        self.bias = bias
        if bias:
            self.bias_term = nn.Parameter(torch.randn(out_features))  #вот тут прописываем смещение

    def forward(self, x:Tensor):
        x =  x @ self.weights.T #считаем часть логита XW
        if self.bias:
            x +=  self.bias_term #добавляем bias
        return x

linear_regression = LinearRegression(2, 1)
loss_function = nn.BCEWithLogitsLoss()
optimizer = torch.optim.SGD(linear_regression.parameters(), lr=0.05)

"""### Задание. Реализация цикла обучения"""

tol = 1e-3
losses = []
max_epochs = 100
prev_weights = torch.zeros_like(linear_regression.weights)
stop_it = False
for epoch in range(max_epochs):
    for it, (X_batch, y_batch) in enumerate(train_dataloader):
        optimizer.zero_grad()
        outp =  linear_regression(X_batch) #считаем предсказания
        loss =  loss_function(outp.flatten(), y_batch) #считаем функцию потерь
        loss.backward()
        losses.append(loss.detach().flatten()[0])
        optimizer.step()
        probabilities =  torch.sigmoid(outp) #переводим предсказания в вероятностный вид
        preds = (probabilities > 0.5).type(torch.long)
        batch_acc = (preds.flatten() == y_batch).type(torch.float32).sum() / y_batch.size(0)

        if (it + epoch * len(train_dataloader)) % 100 == 0:
            print(f"Iteration: {it + epoch * len(train_dataloader)}\nBatch accuracy: {batch_acc}")
        current_weights = linear_regression.weights.detach().clone()
        if (prev_weights - current_weights).abs().max() < tol:
            print(f"\nIteration: {it + epoch * len(train_dataloader)}.Convergence. Stopping iterations.")
            stop_it = True
            break
        prev_weights = current_weights
    if stop_it:
        break

"""### Визуализируем результаты"""

plt.figure(figsize=(12, 8))
plt.plot(range(len(losses)), losses)
plt.xlabel("Iteration")
plt.ylabel("Loss")
plt.show()

import numpy as np

sns.set(style="white")

xx, yy = np.mgrid[-1.5:2.5:.01, -1.:1.5:.01]
grid = np.c_[xx.ravel(), yy.ravel()]
batch = torch.from_numpy(grid).type(torch.float32)
with torch.no_grad():
    probs = torch.sigmoid(linear_regression(batch).reshape(xx.shape))
    probs = probs.numpy().reshape(xx.shape)

f, ax = plt.subplots(figsize=(16, 10))
ax.set_title("Decision boundary", fontsize=14)
contour = ax.contourf(xx, yy, probs, 25, cmap="RdBu",
                      vmin=0, vmax=1)
ax_c = f.colorbar(contour)
ax_c.set_label("$P(y = 1)$")
ax_c.set_ticks([0, .25, .5, .75, 1])

ax.scatter(X[100:,0], X[100:, 1], c=y[100:], s=50,
           cmap="RdBu", vmin=-.2, vmax=1.2,
           edgecolor="white", linewidth=1)

ax.set(xlabel="$X_1$", ylabel="$X_2$")
plt.show()

"""### Задание. Реализуйте predict и посчитайте accuracy на test."""

@torch.no_grad()
def predict(dataloader, model):
    model.eval()
    predictions = np.array([])
    for (x_batch, y_batch) in dataloader:
        preds = torch.sigmoid(model(x_batch)) #считаем предсказания
        predictions = np.hstack((predictions, preds.numpy().flatten()))
    return predictions.flatten()

y_pred_0 = predict(val_dataloader, linear_regression) #массив предсказаний

from sklearn.metrics import accuracy_score
y_true = torch.FloatTensor() #делаем y_true тензором

for (X_batch_test, y_batch_test) in val_dataloader:
  y_true = torch.cat((y_true, y_batch_test), dim=0)

y_pred = torch.as_tensor(y_pred_0, dtype = torch.float32)#предсказания тоже в тензор переводим, чтобы ничего не ломалось

#тут происходит магическое действие, чтобы в дальнейшем мы могли использовать accuracy_score
#наши предсказания мы определяем в один из классов, используя порог 0,5
for i in range(len(y_pred)):
  if y_pred[i] > 0.5:
    y_pred[i]=1
  else:
    y_pred[i]=0

print('Полученныое после обучения значение accuracy: ', accuracy_score(y_true, y_pred))

"""# Часть 2. Датасет MNIST
Датасет MNIST содержит рукописные цифры. Загрузим датасет и создадим DataLoader-ы.
"""

import os
from torchvision.datasets import MNIST
from torchvision import transforms as tfs


data_tfs = tfs.Compose([
    tfs.ToTensor(),
    tfs.Normalize((0.5), (0.5))
])

# установка датасетов
root = './'
train_dataset = MNIST(root, train=True,  transform=data_tfs, download=True)
val_dataset  = MNIST(root, train=False, transform=data_tfs, download=True)

train_dataloader =  torch.utils.data.DataLoader(train_dataset, batch_size=4, #вот тут наш код
                                          shuffle=True, num_workers=2)
valid_dataloader =  torch.utils.data.DataLoader(val_dataset, batch_size=4, #и тут
                                         shuffle=False, num_workers=2)

"""## Часть 2.1. Полносвязные нейронные сети
Сначала решим MNIST с помощью полносвязной нейронной сети.
"""

class Identical(nn.Module):
    def forward(self, x):
        return x

"""### Задание. Простая полносвязная нейронная сеть

Создадим полносвязную нейронную сеть с помощью класса Sequential. Сеть состоит из:
* Уплощения матрицы в вектор (nn.Flatten);
* Двух скрытых слоёв из 128 нейронов с активацией nn.ELU;
* Выходного слоя с 10 нейронами.

Зададим лосс для обучения (кросс-энтропия).

### Задание. Дополните цикл обучения.

### Задание. Протестируйте разные функции активации.
Попробуем разные функции активации. Для каждой функции активации посчитаем массив validation accuracy (лучше реализовать это в виде функции, берущей на вход активацию и получающей массив из accuracies).

Создадим общую функцию для удобства:
"""

#для удобства создадим единую функцию, чтобы тестить разные функции активации
def test_activation_function(activation):

  model = nn.Sequential(
    torch.nn.Flatten(),
    torch.nn.Linear(784, 128),
    activation,
    torch.nn.Linear(128, 128),
    activation,
    torch.nn.Linear(128, 10),
    activation)

  device = "cuda" if torch.cuda.is_available() else "cpu"

  model = model.to(device)
  criterion = torch.nn.CrossEntropyLoss()
  optimizer = torch.optim.Adam(model.parameters())

  loaders = {"train": train_dataloader, "valid": valid_dataloader}

  max_epochs = 10

  accuracy = {"train": [], "valid": []}

  for epoch in range(max_epochs):
    for k, dataloader in loaders.items():
        epoch_correct = 0
        epoch_all = 0
        for x_batch, y_batch in dataloader:
            if k == "train":
                model.train()
                optimizer.zero_grad()
                outp = model(x_batch.to(device))
                loss = criterion(outp, y_batch.to(device))
                loss.backward()
                optimizer.step()
            else:
                model.eval()
                with torch.no_grad():
                    outp = model(x_batch.to(device))
            preds = outp.argmax(-1)
            correct = (preds == y_batch.to(device)).sum()
            all = y_batch.to(device).size(0)
            epoch_correct += correct.item()
            epoch_all += all

        if k == "train":
            print(f"Epoch: {epoch+1}")

        print(f"Loader: {k}. Accuracy: {epoch_correct/epoch_all}")
        accuracy[k].append(epoch_correct/epoch_all)

  return accuracy["valid"]

leaky_relu_accuracy = test_activation_function(torch.nn.LeakyReLU())

elu_accuracy = test_activation_function(torch.nn.ELU())

plain_accuracy = test_activation_function(Identical())

relu_accuracy = test_activation_function(torch.nn.ReLU())

"""### Accuracy
Построим график accuracy/epoch для каждой функции активации.
"""

sns.set(style="darkgrid", font_scale=1.4)

plt.figure(figsize=(16, 10))
plt.title("Valid accuracy")
plt.plot(range(10), plain_accuracy, label="No activation", linewidth=2)
plt.plot(range(10), relu_accuracy, label="ReLU activation", linewidth=2)
plt.plot(range(10), leaky_relu_accuracy, label="LeakyReLU activation", linewidth=2)
plt.plot(range(10), elu_accuracy, label="ELU activation", linewidth=2)
plt.legend()
plt.xlabel("Epoch")
plt.show()

"""Наивысший `accuracy` к концу обучения показала функция активации ELU, но они достаточно схожи по результатам с LeakyReLU.

## Часть 2.2 Сверточные нейронные сети

### Задание. Реализуйте LeNet

Если мы сделаем параметры сверток обучаемыми, то можем добиться хороших результатов для задач компьютерного зрения. Реализуем архитектуру LeNet,
используя модульную структуру (без помощи класса Sequential).

Наша нейронная сеть будет состоять из
* Свёртки 3x3 (1 карта на входе, 6 на выходе) с активацией ReLU;
* MaxPooling-а 2x2;
* Свёртки 3x3 (6 карт на входе, 16 на выходе) с активацией ReLU;
* MaxPooling-а 2x2;
* Уплощения (nn.Flatten);
* Полносвязного слоя со 120 нейронами и активацией ReLU;
* Полносвязного слоя с 84 нейронами и активацией ReLU;
* Выходного слоя из 10 нейронов.
"""

data_tfs = tfs.Compose([
    tfs.ToTensor(),
    tfs.Normalize((0.5), (0.5))
])


root = './'
train_dataset = MNIST(root, train=True,  transform=data_tfs, download=True)
val_dataset  = MNIST(root, train=False, transform=data_tfs, download=True)

train_dataloader =  torch.utils.data.DataLoader(train_dataset, batch_size=4,
                                          shuffle=True, num_workers=2)
valid_dataloader =  torch.utils.data.DataLoader(val_dataset, batch_size=4,
                                         shuffle=False, num_workers=2)

#собираем сверточную нейронную сеть
class LeNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=6, kernel_size=3)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2) #пуллинг 2x2
        self.conv2 = nn.Conv2d(in_channels=6, out_channels=16, kernel_size=3) #свертка 3x3, 6 на вход, 16 на выход
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2) #пуллинг 2x2
        self.fc1 = nn.Linear (400,120) #16*5*5 - входной, 120 нейронов на первом слое
        self.fc2 = nn.Linear (120,84) #84 нейрона на втором слое
        self.fc3 = nn.Linear (84,10) #10 нейронов - выходной

    def forward(self, x):
        #проворачиваем все функции активации
        x = self.pool1(F.relu(self.conv1(x)))
        x = self.pool2(F.relu(self.conv2(x)))
        #print(x.shape)
        x = x.view(-1, 400) #вместо Flatten
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x

device = "cuda" if torch.cuda.is_available() else "cpu"
model = LeNet().to(device)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters())

loaders = {"train": train_dataloader, "valid": valid_dataloader}

"""### Задание. Обучите CNN

"""

#используем тот же код, что и для полносвязной
max_epochs = 10
accuracy = {"train": [], "valid": []}
for epoch in range(max_epochs):
 for k, dataloader in loaders.items():
  epoch_correct = 0
  epoch_all = 0

  for x_batch, y_batch in dataloader:
    if k == "train":
      model.train()
      optimizer.zero_grad()
      outp = model(x_batch.to(device))

      loss = criterion(outp, y_batch.to(device))
      loss.backward()
      optimizer.step()
    else:
      model.eval()
      with torch.no_grad():
        outp = model(x_batch.to(device))
    preds = outp.argmax(-1)
    correct = (preds == y_batch.to(device)).sum()
    all = y_batch.to(device).size(0)
    epoch_correct += correct.item()
    epoch_all += all

  if k == "train":
    print(f"Epoch: {epoch+1}")

  print(f"Loader: {k}. Accuracy: {epoch_correct/epoch_all}")
  accuracy[k].append(epoch_correct/epoch_all)

lenet_accuracy = accuracy["valid"]
print(lenet_accuracy)

"""Сравним с предыдущем пунктом."""

#тут строим все графики

plt.figure(figsize=(16, 10))
plt.title("Valid accuracy")
plt.plot(range(max_epochs), relu_accuracy, label="ReLU activation", linewidth=2)
plt.plot(range(max_epochs), leaky_relu_accuracy, label="LeakyReLU activation", linewidth=2)
plt.plot(range(max_epochs), elu_accuracy, label="ELU activation", linewidth=2)
plt.plot(range(max_epochs), lenet_accuracy, label="LeNet", linewidth=2)
plt.plot(range(max_epochs), plain_accuracy, label="No activation", linewidth=2)
plt.legend()
plt.xlabel("Epoch")
plt.show()

"""LeNet в сравнении с полносвязными сетями показал наилучший результат, `accuracy = 0,99`"""