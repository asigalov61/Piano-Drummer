# -*- coding: utf-8 -*-
"""Piano_Drummer.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/11SbwUHL2UG_w9V0n9MxbNkUG71QHokXb

# Piano Drummer (ver. 0.5)

***

Powered by tegridy-tools: https://github.com/asigalov61/tegridy-tools

***

Credit for GPT2-RGA code used in this colab goes out @ Sashmark97 https://github.com/Sashmark97/midigen and @ Damon Gwinn https://github.com/gwinndr/MusicTransformer-Pytorch

***

WARNING: This complete implementation is a functioning model of the Artificial Intelligence. Please excercise great humility, care, and respect. https://www.nscai.gov/

***

#### Project Los Angeles

#### Tegridy Code 2022

***
"""

#@title nvidia-smi gpu check
!nvidia-smi

#@title Install all dependencies (run only once per session)

!git clone https://github.com/asigalov61/tegridy-tools

!pip install torch

!pip install tqdm
!pip install matplotlib
!pip install torch-summary

!apt install fluidsynth #Pip does not work for some reason. Only apt works
!pip install midi2audio
!pip install pretty_midi

#@title Import all needed modules

print('Loading needed modules. Please wait...')
import os
import random
from collections import OrderedDict
import copy
from tqdm import tqdm

import matplotlib.pyplot as plt

from torchsummary import summary

if not os.path.exists('/content/Dataset'):
    os.makedirs('/content/Dataset')

print('Loading TMIDIX module...')
os.chdir('/content/tegridy-tools/tegridy-tools')
import TMIDIX

os.chdir('/content/tegridy-tools/tegridy-tools')
from GPT2RGAX import *

from midi2audio import FluidSynth
import pretty_midi
import librosa.display
from IPython.display import Audio

os.chdir('/content/')

"""# Download MIDI dataset

<iframe src="https://onedrive.live.com/embed? width="98" height="120" frameborder="0" scrolling="no"></iframe>
"""

#@title Rock-Piano Dataset
!wget --no-check-certificate -O 'Rock-Piano.zip' "https://onedrive.live.com/download?cid=8A0D502FC99C608F&resid=8A0D502FC99C608F%2118570&authkey=APv5HBxyoa5LAPo"
!unzip Rock-Piano.zip

"""# Process"""

#@title Process MIDIs

sorted_or_random_file_loading_order = True # Sorted order is NOT usually recommended
dataset_ratio = 1 # Change this if you need more data


print('TMIDIX MIDI Processor')
print('Starting up...')
###########

files_count = 0

gfiles = []

chords_f = []

###########

print('Loading MIDI files...')
print('This may take a while on a large dataset in particular.')

dataset_addr = "./Rock-Piano/"
# os.chdir(dataset_addr)
filez = list()
for (dirpath, dirnames, filenames) in os.walk(dataset_addr):
    filez += [os.path.join(dirpath, file) for file in filenames]
print('=' * 70)

if filez == []:
    print('Could not find any MIDI files. Please check Dataset dir...')
    print('=' * 70)

if sorted_or_random_file_loading_order:
    print('Sorting files...')
    filez.sort()
    print('Done!')
    print('=' * 70)
else:
    print('Randomizing file list...')
    random.shuffle(filez)


print('Processing MIDI files. Please wait...')
for f in tqdm(filez[:int(len(filez) * dataset_ratio)]):
    try:
      fn = os.path.basename(f)
      fn1 = fn.split('.')[0]

      files_count += 1

      #print('Loading MIDI file...')
      score = TMIDIX.midi2ms_score(open(f, 'rb').read())

      itrack = 1

      events_matrix1 = []

      while itrack < len(score):
          for event in score[itrack]:         
              if event[0] == 'note':
                  events_matrix1.append(event)
          itrack += 1

      # final processing...

      if len(events_matrix1) > 0:

          events_matrix1.sort(key=lambda x: x[4], reverse=True) # Sort by pitch H -> L
          events_matrix1.sort(key=lambda x: x[1]) # Then sort by start-times
          

          chords = []
          cho = []
          pe = events_matrix1[0]
          for e in events_matrix1: 
              if abs(e[1] - pe[1]) == 0:
                cho.append(e)
              else:
                chords.append(cho)
                cho = []
                cho.append(e)

              pe = e

      chords_f.append(chords)    

      gfiles.append(f)

    except KeyboardInterrupt:
        print('Saving current progress and quitting...')
        break  

    except:
        print('Bad MIDI:', f)
        continue

#@title Save
TMIDIX.Tegridy_Any_Pickle_File_Writer(chords_f, '/content/Rock-Piano-DATA')

"""# Prep DATA"""

#@title Load
chords_f = TMIDIX.Tegridy_Any_Pickle_File_Reader('/content/Rock-Piano-DATA')

#@title Process
DATA = []

for c in tqdm(chords_f):

  DATA.extend([127, 512]) # Intro/Zero tokens pair (time == 127, drums pitch == 0+512)

  pchord = c[0]

  time = 0

  for cc in c:

    piano_events = [y for y in cc if y[3] == 0]
    piano_events_length = len(piano_events)

    drums_events = [y for y in cc if y[3] == 9]
    drums_events_length = len(drums_events)

    time = max(0, min(127, int(abs(cc[0][1] - pchord[0][1]) / 5)))

    # Empty (0+) - Pause (128+) - Note (256+) - Chord (386+) == Total of 512 range

    # Drums pitches == 512+

    # Total of 640 range

    if piano_events_length == 0 and drums_events_length != 0: # No piano, drums present (Empty)

      for e in drums_events:
        if drums_events.index(e) == 0:
          DATA.extend([time, e[4]+512])
        else:
          DATA.extend([0, e[4]+512])

    if piano_events_length != 0 and drums_events_length == 0: # Piano present, no drums (Pause)
        DATA.extend([time+128, 0+512])

    if piano_events_length != 0 and drums_events_length != 0: # Piano note present, drums present (Note)
      if piano_events_length == 1:
        for e in drums_events:
          if drums_events.index(e) == 0:
            DATA.extend([time+256, e[4]+512])
          else:
            DATA.extend([0+256, e[4]+512])

    if piano_events_length != 0 and drums_events_length != 0: # Piano chord present, drums present (Chord)
      if piano_events_length > 1:
        for e in drums_events:
          if drums_events.index(e) == 0:
            DATA.extend([time+386, e[4]+512])
          else:
            DATA.extend([0+386, e[4]+512])

    pchord = cc

#@title Save
TMIDIX.Tegridy_Any_Pickle_File_Writer(DATA, '/content/Rock-Piano-INTs')

"""# Training"""

#@title Load
DATA = TMIDIX.Tegridy_Any_Pickle_File_Reader('/content/Rock-Piano-INTs')
train_data1 = DATA

#@title Load processed INTs dataset

SEQ_LEN = max_seq

BATCH_SIZE = 8 # Change this to your specs

# DO NOT FORGET TO ADJUST MODEL PARAMS IN GPT2RGAX module to your specs

print('=' * 50)
print('Loading training data...')

data_train, data_val = torch.LongTensor(train_data1[:-(SEQ_LEN * (BATCH_SIZE))]), torch.LongTensor(train_data1[-(SEQ_LEN * (BATCH_SIZE))-1:])

class MusicSamplerDataset(Dataset):
    def __init__(self, data, seq_len):
        super().__init__()
        self.data = data
        self.seq_len = seq_len

    def __getitem__(self, index):
        rand = random.randint(0, (self.data.size(0)-self.seq_len) // self.seq_len) * self.seq_len
        x = self.data[rand: rand + self.seq_len].long()
        trg = self.data[(rand+1): (rand+1) + self.seq_len].long()
        return x, trg

    def __len__(self):
        return self.data.size(0)

train_dataset = MusicSamplerDataset(data_train, SEQ_LEN)
val_dataset   = MusicSamplerDataset(data_val, SEQ_LEN)
train_loader  = DataLoader(train_dataset, batch_size = BATCH_SIZE)
val_loader    = DataLoader(val_dataset, batch_size = BATCH_SIZE)

print('Total INTs in the dataset', len(train_data1))
print('Total unique INTs in the dataset', len(set(train_data1)))
print('Max INT in the dataset', max(train_data1))
print('Min INT in the dataset', min(train_data1))
print('=' * 50)

print('Length of the dataset:',len(train_dataset))
print('Number of dataset samples:', (len(train_dataset) // SEQ_LEN))
print('Length of data loader',len(train_loader))
print('=' * 50)
print('Done! Enjoy! :)')
print('=' * 50)

#@title Check dataloader for errors
for x, trg in train_loader:
  print(len(x), len(trg))

"""# Train"""

#@title Train the model

DIC_SIZE = 640

# DO NOT FORGET TO ADJUST MODEL PARAMS IN GPT2RGAX module to your specs

config = GPTConfig(DIC_SIZE, 
                   max_seq,
                   dim_feedforward=1024,
                   n_layer=6, 
                   n_head=8, 
                   n_embd=640,
                   enable_rpr=True,
                   er_len=max_seq)

# DO NOT FORGET TO ADJUST MODEL PARAMS IN GPT2RGAX module to your specs

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = GPT(config)

model = nn.DataParallel(model) # Multi-GPU training...

model.to(device)

#=====

init_step = 0
lr = LR_DEFAULT_START
lr_stepper = LrStepTracker(d_model, SCHEDULER_WARMUP_STEPS, init_step)
eval_loss_func = nn.CrossEntropyLoss(ignore_index=DIC_SIZE)
train_loss_func = eval_loss_func

opt = Adam(model.parameters(), lr=lr, betas=(ADAM_BETA_1, ADAM_BETA_2), eps=ADAM_EPSILON)
lr_scheduler = LambdaLR(opt, lr_stepper.step)


#===

best_eval_acc        = 0.0
best_eval_acc_epoch  = -1
best_eval_loss       = float("inf")
best_eval_loss_epoch = -1
best_acc_file = '/content/gpt2_rpr_acc.pth'
best_loss_file = '/content/gpt2_rpr_loss.pth'
loss_train, loss_val, acc_val = [], [], []

for epoch in range(0, epochs):
    new_best = False
    
    loss = train(epoch+1, 
                 model, train_loader, 
                 train_loss_func, 
                 opt, 
                 lr_scheduler, 
                 num_iters=-1, 
                 save_checkpoint_steps=4000)
    
    loss_train.append(loss)
    
    eval_loss, eval_acc = eval_model(model, val_loader, eval_loss_func, num_iters=-1)
    loss_val.append(eval_loss)
    acc_val.append(eval_acc)
    
    if(eval_acc > best_eval_acc):
        best_eval_acc = eval_acc
        best_eval_acc_epoch  = epoch+1
        torch.save(model.state_dict(), best_acc_file)
        new_best = True

    if(eval_loss < best_eval_loss):
        best_eval_loss       = eval_loss
        best_eval_loss_epoch = epoch+1
        torch.save(model.state_dict(), best_loss_file)
        new_best = True
    
    if(new_best):
        print("Best eval acc epoch:", best_eval_acc_epoch)
        print("Best eval acc:", best_eval_acc)
        print("")
        print("Best eval loss epoch:", best_eval_loss_epoch)
        print("Best eval loss:", best_eval_loss)

"""# (MODEL SAVE/LOAD)"""

#@title Save the model

print('Saving the model...')
full_path_to_model_checkpoint = "/content/Piano-Drummer-Trained-Model.pth" #@param {type:"string"}
torch.save(model.state_dict(), full_path_to_model_checkpoint)
print('Done!')

#@title Load/Reload the model

full_path_to_model_checkpoint = "/content/Piano-Drummer-Trained-Model.pth" #@param {type:"string"}

print('Loading the model...')
config = GPTConfig(640, 
                   max_seq,
                   dim_feedforward=1024,
                   n_layer=8, 
                   n_head=8, 
                   n_embd=640,
                   enable_rpr=True,
                   er_len=max_seq)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = GPT(config)

state_dict = torch.load(full_path_to_model_checkpoint, map_location=device)

new_state_dict = OrderedDict()
for k, v in state_dict.items():
    name = k[7:] #remove 'module'
    new_state_dict[name] = v

model.load_state_dict(new_state_dict)

model.to(device)

model.eval()

print('Done!')

summary(model)

"""# Generate"""

#@title Load source piano composition

full_path_to_custom_MIDI = "/content/tegridy-tools/tegridy-tools/seed2.mid"

print('Loading custom MIDI file...')

score = TMIDIX.midi2ms_score(open(full_path_to_custom_MIDI, 'rb').read())

events_matrix1 = []

itrack = 1

while itrack < len(score):
    for event in score[itrack]:         
        if event[0] == 'note' and event[3] != 9:
            events_matrix1.append(event)
    itrack += 1


events_matrix1.sort(key=lambda x: x[4], reverse=True) # Sort by pitch H -> L
events_matrix1.sort(key=lambda x: x[1]) # Then sort by start-times

if len(events_matrix1) > 0:

    # recalculating timings

    for e in events_matrix1:
        e[1] = int(e[1] / 5)
        e[2] = int(e[2] / 10)
    
    # final processing...
    melody_chords = []
    
    pe = events_matrix1[0]

    for e in events_matrix1:

        time = max(0, min(127, e[1]-pe[1])) # Time-shift
        dur = max(0, min(127, e[2])) # Duration
        ptc = max(0, min(127, e[4])) # Pitch
        vel = max(0, min(127, e[5]))

        melody_chords.append([time, dur, ptc, vel])

        pe = e

ctimes = []
       
chords = []
cho = []
for m in melody_chords:
  if m[0] == 0:
    cho.append(m)
  else:
    chords.append(cho)

    if len(cho) == 1:
      ctimes.append(cho[0][0]+256)
    else:
      ctimes.append(cho[0][0]+386)


    cho = []
    cho.append(m)

print('Done!')

"""## Simple Generator"""

out = zt + [ctimes[0]]

drums1 = []

for i in tqdm(range(500)):

  rand_seq = model.generate(torch.Tensor(out), 
                                        target_seq_length=len(out)+1,
                                        temperature=1,
                                        stop_token=640,
                                        verbose=False)

  out1 = rand_seq[0].cpu().numpy().tolist()
  out.append(out1[-1])
  drums1.append(out1[-1])
  out.append(ctimes[i+1])

song = chords[:500]
song_f = []
time = 0
dur = 0
vel = 0
pitch = 0
channel = 0
son = []
idx = 0
for s in song:
  time += s[0][0] * 5
  for ss in s:

    

    dur = ((ss[1]) * 10) + 10
    
    channel = 0 # Piano

    pitch = ss[2]
    
    vel = ss[3] # Note velocity == note pitch value

                        
    song_f.append(['note', time, dur, channel, pitch, vel ])
    
  channel = 9 # Piano

  pitch = drums1[idx] - 512

  song_f.append(['note', time, dur, channel, pitch, 90 ])

  idx += 1

detailed_stats = TMIDIX.Tegridy_SONG_to_MIDI_Converter(song_f,
                                                    output_signature = 'Piano Drummer',  
                                                    output_file_name = '/content/Piano-Drummer-Music-Composition', 
                                                    track_name='Project Los Angeles',
                                                    list_of_MIDI_patches=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                                    number_of_ticks_per_quarter=500)

print('Done!')

"""# Advanced Generator"""

number_of_tokens_per_note = 9 # Must be odd for now...
number_of_memory_tokens = 128
time_k = 4
model_temperature = 0.8

out = copy.deepcopy([ctimes[0]])

for i in tqdm(range(len(ctimes)-1)):

    rand_seq = model.generate(torch.Tensor(out[-number_of_memory_tokens+number_of_tokens_per_note:]), 
                                          target_seq_length=(len(out[-(number_of_memory_tokens-number_of_tokens_per_note):])+number_of_tokens_per_note),
                                          temperature=model_temperature,
                                          stop_token=640,
                                          verbose=False)

    out1 = rand_seq[0].cpu().numpy().tolist()

    time = 0
    next = ctimes[i+1] % 128
    k = ctimes[i+1] // 128
    count = 0
    tdelta = next

    for j in [y % 128 for y in out1[-(number_of_tokens_per_note-1):][0::2]]:
      
      time += j
      
      if time+time_k >= next:
        break

      tdelta = next - time      
      count += 1

    out.extend(out1[-(number_of_tokens_per_note):][:(count*2)+1])

    out.append(((k * 128) + tdelta))

song = chords
song_f = []
time = 0
dur = 0
vel = 0
pitch = 0
channel = 0

count = 0
for s in song:

  time += (ctimes[count] % 128) * 5
  count += 1
  for ss in s:

    dur = ((ss[1]) * 10) + 10
    
    channel = 0 # Piano

    pitch = ss[2]
    
    vel = ss[3] # Note velocity == note pitch value

                        
    song_f.append(['note', time, dur, channel, pitch, vel ])

time = 0
dur = 0

for o in out:

  if o < 512:
    time += (o % 128) * 5
    dur = (o % 128) * 10
  else:
    if o > 512:

      channel = 9 # Drums

      pitch = o - 512

      vel = 90

      song_f.append(['note', time, dur, channel, pitch, 90 ])

song_f.sort(key=lambda x: x[1])

detailed_stats = TMIDIX.Tegridy_SONG_to_MIDI_Converter(song_f,
                                                    output_signature = 'Piano Drummer',  
                                                    output_file_name = '/content/Piano-Drummer-Music-Composition', 
                                                    track_name='Project Los Angeles',
                                                    list_of_MIDI_patches=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                                    number_of_ticks_per_quarter=500)

print('Done!')

"""# Colab MIDI player and plotter"""

print('Displaying resulting composition...')
fname = '/content/Piano-Drummer-Music-Composition'

pm = pretty_midi.PrettyMIDI(fname + '.mid')

# Retrieve piano roll of the MIDI file
piano_roll = pm.get_piano_roll()

plt.figure(figsize=(14, 5))
librosa.display.specshow(piano_roll, x_axis='time', y_axis='cqt_note', fmin=1, hop_length=160, sr=16000, cmap=plt.cm.hot)
plt.title(fname)

FluidSynth("/usr/share/sounds/sf2/FluidR3_GM.sf2", 16000).midi_to_audio(str(fname + '.mid'), str(fname + '.wav'))
Audio(str(fname + '.wav'), rate=16000)