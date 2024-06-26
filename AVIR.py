# -*- coding: utf-8 -*-
"""Integration.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1-mdujOOKSsjWDW4vT1L8XmbzdqzaFcNs
"""

!pip install onnxruntime
!pip install -U keras
!pip install onnx
!pip install -U tf2onnx
!pip install mlprodict

class BlockData:
  def __init__(self, block_id):
    self.block_id = block_id # 현재 블록 인덱스
    self.avg_memory_peak = -1.0
    self.avg_duration = -1.0

  def profiling_update(self, memory, duration):
    self.avg_memory_peak = memory
    self.avg_duration = duration

class Edge:
  def __init__(self, prev, curr):
    self.prev_block_id = prev # 이전 블록 인덱스
    self.curr_block_id = curr # 현재 블록 인덱스

from tensorflow import keras
import numpy as np

epochs_num = 1

fmnist = keras.datasets.fashion_mnist
(x_train,y_train), (x_test, y_test) = fmnist.load_data()

sequential_model = keras.models.Sequential([
    keras.layers.Flatten(input_shape = (28,28)),
    keras.layers.Dense(1024, activation = 'relu'),
    keras.layers.Dense(512, activation = 'relu'),
    keras.layers.Dense(36, activation = 'relu'),
    keras.layers.Dense(64, activation = 'relu'),
    keras.layers.Dense(14, activation = 'relu'),
    keras.layers.Dense(64, activation = 'relu'),
    keras.layers.Dense(14, activation = 'relu'),
    keras.layers.Dense(64, activation = 'relu'),
    keras.layers.Dense(74, activation = 'relu'),
    keras.layers.Dense(64, activation = 'relu'),
    keras.layers.Dense(80, activation = 'relu'),
    keras.layers.Dense(64, activation = 'relu'),
    keras.layers.Dense(140, activation = 'relu'),
    keras.layers.Dense(10, activation = 'softmax'),
])

sequential_model.compile(optimizer = 'adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
hist = sequential_model.fit(x_train,y_train, epochs = epochs_num, validation_data = (x_test, y_test))

sequential_model.summary()

from tensorflow.keras.applications import VGG16
import tensorflow as  tf

# VGG-16 모델 save
vgg_model = VGG16(weights='imagenet')
vgg_model.summary()

from tensorflow.keras.applications import ResNet50
import tensorflow as  tf

# ResNet50 모델 save
resnet_model = ResNet50(weights='imagenet')
resnet_model.summary()

from keras.src.models import Functional
from keras.src.models import Sequential
import tree
def flow_control(model):
  if isinstance(model, Sequential):
      sequential_like = True
      layers = model.layers
  elif not isinstance(model, Functional):
      sequential_like = True
      layers = model.layers
  else:
      layers = model._operations
      sequential_like = True
      nodes_by_depth = model._nodes_by_depth.values()
      nodes = []
      for v in nodes_by_depth:
          if (len(v) > 1) or (
              len(v) == 1 and len(tree.flatten(v[0].input_tensors)) > 1
          ):
              sequential_like = False
              break
          nodes += v
      if sequential_like:
          for layer in model.layers:
              flag = False
              for node in layer._inbound_nodes:
                  if node in nodes:
                      if flag:
                          sequential_like = False
                          break
                      else:
                          flag = True
              if not sequential_like:
                  break
  if isinstance(model, Sequential):
    relevant_nodes = []
  else:
    relevant_nodes = []
    for v in model._nodes_by_depth.values():
        relevant_nodes += v
  return relevant_nodes

def get_connections(layer, relevant_nodes):
    connections = ""
    for node in layer._inbound_nodes:
        if relevant_nodes and node not in relevant_nodes:
            continue
        for kt in node.input_tensors:
            keras_history = kt._keras_history
            inbound_layer = keras_history.operation
            if connections:
                connections += ", "
            connections += (
                f"{inbound_layer.name}"
            )
    if not connections:
        connections = "-"
    return connections

import tensorflow as tf
import numpy as np
from keras.models import Sequential, Model
from tensorflow.keras import layers

def mk_rand_input(model_input):
  input = np.random.rand(1, *model_input.layers[1].input.shape[1:])
  return input

def clip_model(model_input, start, end):
  while(isinstance(model_input.layers[start], layers.InputLayer)):
    start +=1
  new_model = tf.keras.models.Model(inputs=model_input.layers[start].input, outputs=model_input.layers[end].output)
  return new_model

def mk_idx_dict(model):
  index_dictionary = {}
  for i in range(0,len(model.layers)):
    index_dictionary[model.layers[i].name] = i
  return index_dictionary

def layer_flow_analysis(model, index_dictionary, relevant, max_block_size):
  # 흐름 분석 코드
  # flow_dictionary = {} # 블록의 시작 레이어를 key로 끝 레이어를 value로 가짐, 단일 흐름이 되는 부분들을 저장
  end_list = [] # 블록의 끝 레이어의 인덱스를 저장
  start_list = [] # 블록의 시작 레이어의 인덱스를 저장
  count_list = [0 for _ in range(len(model.layers))] # 길이가 모델의 레이어 수와 같은 리스트 생성
  # 출력이 여러개인 레이어 확인 위해서는 레이어들의 입력 카운트 필요
  # 레이어의 입력 레이어의 인덱스 확인 index_dictionary[입력 레이어 이름]

  start_idx = 0
  for i in range(0,len(model.layers)-1):
    layer_name = get_connections(model.layers[i+1], relevant)
    names = layer_name.split(", ")
    for name in names:
      count_list[index_dictionary[name]] += 1
    if model.layers[i].name == layer_name: # i번 레이어와 i+1레이어가 단일 흐름인지 확인
      if(i == len(model.layers)-2): # 모델의 마지막 레이어에 도달한 경우
        start_list.append(start_idx)
        end_list.append(i+1)
    else:
      start_list.append(start_idx)
      end_list.append(i)
      start_idx = i + 1
      if(i == len(model.layers)-2):# 모델의 마지막 레이어에 도달한 경인
        start_list.append(start_idx)
        end_list.append(i)
  additional_list = [] #
  for i in range(0,len(count_list)-1):
    if count_list[i] !=1:
      additional_list.append(i)
  for i in additional_list:
    start_list.append(i+1)
    end_list.append(i)
  start_list = sorted(list(set(start_list)))
  end_list = sorted(list(set(end_list)))

  e_list = []
  s_list = []
  turn = True
  while(turn):
    turn = False
    for i in range(0, len(start_list)):
      block_size = end_list[i] - start_list[i]
      if block_size >= max_block_size:
        turn = True
        # 일단 대충 썼음 적당히 다시 숫자 조정
        s_list.append(start_list[i] + int(block_size/2))
        e_list.append(start_list[i] + int(block_size/2)-1)
      #기존의 리스트에 합치고 다시 중복 제거 및 정렬
      start_list.extend(s_list)
      end_list.extend(e_list)
      start_list = sorted(list(set(start_list)))
      end_list = sorted(list(set(end_list)))
  return start_list, end_list

import bisect
def mk_block(model, index_dictionary, relevant):
  start_list, end_list = layer_flow_analysis(model, index_dictionary, relevant, 5) # 최대 블록 크기를 5로 설정, 변경 가능
  block_connect_N = [] # 마지막 블록(즉 마지막 블록은 [-1])
  block_connect_P = [] # 처음 블록(즉 입력 시작 블록은 [-1])

  for i in range(0, len(start_list)):
    block_connect_N.append([])
    block_connect_P.append([])

  block_connect_P[0].append(-1) # 처음 블록 [-1]
  for i in range(1, len(start_list)):
    index_of_pLayer = []
    pLayer_names = get_connections(model.layers[start_list[i]], relevant).split(", ")
    for pName in pLayer_names:
      index_of_pLayer.append(index_dictionary[pName])
      # 여기 인덱스 번호가 이전 레이어의 인덱스 번호

    for idx in index_of_pLayer:
      block_index = bisect.bisect_left(end_list, idx)
      block_connect_P[i].append(block_index)
      block_connect_N[block_index].append(i)
  block_connect_N[-1].append(-1) # 마지막 블록 [-1]
  # start_lilst, flow_dictionary를 이용해서 단일 흐름을 한 블록으로 만듦,
  # 실제 사용 시에는 단일 흐름 내에서도 여러 조각의 블록으로 분할해야한다.
  model_list = []
  for i in range(0,len(start_list)):
    model_list.append(clip_model(model,start_list[i],end_list[i]))

  return block_connect_N, block_connect_P, model_list

# 시각화에 쓸 블록 리스트, 엣지 리스트 반환
def visualization_data(block_connect_P):
  block_list = []
  edge_list = []
  for curr_idx in range(len(block_connect_P) - 1, -1, -1):
    block_list.append(BlockData(curr_idx))

  for curr_idx in range(len(block_connect_P)):
    prev_list = block_connect_P[curr_idx]
    for prev_idx in prev_list:
      edge_list.append(Edge(prev_idx, curr_idx))

  return block_list, edge_list

from threading import Thread

class ReturnValueThread(Thread):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

# 메모리 프로파일링을 위한 함수
import tracemalloc  # 메모리 프로파일링을 위한 모듈

def memory_profiling():
    tracemalloc.start(100)  # 트레이스할 스택 프레임의 개수 지정
    max_memory_usage = 0
    while not exit_flag:  # 종료 플래그가 설정될 때까지 계속 실행
        current, peak = tracemalloc.get_traced_memory()
        max_memory_usage = max(max_memory_usage, peak)  # 최댓값 갱신
        time.sleep(0.01)
    return max_memory_usage  # 최댓값 반환

# 모델 입력 생성

input = []
iter = 4 # 프로파일링 횟수
for i in range(iter):
  input.append(mk_rand_input(resnet_model))
print(input)

# 모델 분할
relevant = flow_control(resnet_model)
index_dictionary = mk_idx_dict(resnet_model)

block_connect_N, block_connect_P, model_list = mk_block(resnet_model, index_dictionary, relevant)
print(block_connect_N)
print(block_connect_P)

# 분할된 모델 저장
count = 0
for i in model_list:
  tf.saved_model.save(i, ("test_model0012/model" + str(count)))
  count +=1

import subprocess

# ONNX 모델로 변환
model_name = "test_model0012"
input_name = "model"
output_name = "model"
extension = ".onnx"
for i in range(0, len(model_list)):
  input_cli = model_name + "/" +input_name + str(i)
  output_cli = model_name + "_onnxfile" + "/" +output_name + str(i) + extension
  command = [
      "python",
      "-m",
      "tf2onnx.convert",
      "--saved-model",
      input_cli,
      "--output",
      output_cli,
      "--opset",
      "13"
  ]
  print(command)
  # CLI 명령 실행
  subprocess.run(command)

# 프로파일링 수행
import numpy as np
from mlprodict.onnxrt import OnnxInference
import threading
import time
import torch

# 프로파일링
output = []
dur_list = []
mem_list = []

for j in range(len(input)):
  ort_list = []
  for i in range(0, len(model_list)):
    ort_list.append(OnnxInference(model_name + "_onnxfile" + "/" +"model" + str(i) + extension, runtime="onnxruntime1", runtime_options={"enable_profiling": True}))
    tracemalloc.clear_traces()
    # 종료 플래그
    exit_flag = False

    # 프로파일링 스레드 시작
    profiling_thread = ReturnValueThread(target=memory_profiling)
    profiling_thread.start()

    # 메인 프로그램 실행
    if block_connect_P[i][0] == -1: # 원본 모델의 input layer가 있는 블록
      output.append(ort_list[i].run({ort_list[i].input_names[0]: input[j].astype(np.float32)}))
    else:
      input_dict = {}
      for k in range(len(block_connect_P[i])):
        input_dict[ort_list[i].input_names[k]] = np.array(list(output[block_connect_P[i][k]].values()))[0].astype(np.float32)
      output.append(ort_list[i].run(input_dict))

    # 종료 플래그 설정 및 프로파일링 스레드 종료 대기
    exit_flag = True

    mem_list.append([])
    dur_list.append([])
    max_memory_usage= profiling_thread.join()  # 스레드 종료 대기
    mem_list[j].append(max_memory_usage)
    profiling_info = ort_list[i].get_profiling(as_df = True)
    dur_list[j].append(profiling_info.dur.sum(axis=0))

    # 스레드 삭제
    del profiling_thread

sum_dur = []
sum_mem = []
avg_dur = []
avg_mem = []
for i in range(0, len(model_list)):
  sum_dur.append(0)
  sum_mem.append(0)
  for j in range(len(input)):
    sum_dur[i] += dur_list[j][i]
    sum_mem[i] += mem_list[j][i]
  avg_dur.append(sum_dur[i]/len(input))
  avg_mem.append(sum_mem[i]/len(input))

# 프로파일링 결과를 시각화에 사용할 형태로 저장
for i in range(len(avg_dur)):
  list_N = block_connect_N[i]
  str_N = "[" + str(list_N[0])
  list_P = block_connect_P[i]
  str_P = "[" + str(list_P[0])
  for j in range(1, len(list_N)):
    str_N = str_N + " " + str(list_N[j])
  for j in range(1, len(list_P)):
    str_P = str_P + " " + str(list_P[j])
  print("(" + str(i) + ", " + str(avg_dur[i]) + ", " + str(avg_mem[i]) + ", " + str_N + "], " + str_P + "])")

from tensorflow.keras.utils import plot_model

plot_model(resnet_model)

