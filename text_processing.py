import numpy as np
import pandas
import pandas as pd
import regex as re
import re
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from argparse import Namespace

class Vocabulary:
    '''Contains dictionary of tokens and their indices'''
    def __init__(self, token_to_idx : dict = None, is_unk_token : bool = True, unk_token : str = '<UNK>'):
        if token_to_idx is None:
            token_to_idx = {}
        self._token_to_idx = token_to_idx
        self._idx_to_token = {idx : token for token, idx in token_to_idx.items()}
        
        self._is_unk_token = is_unk_token
        self._unk_token = unk_token
        self.unk_index = -1

        if is_unk_token:
            self.unk_index = self.add_token(unk_token)

    def __len__(self) -> int:
        return len(self._token_to_idx)

    def to_serializable(self) -> dict:
        return {'token_to_idx' : self._token_to_idx, 'is_unk_token' : self._is_unk_token, 'unk_token' : self._unk_token}
    
    def to_json(self, filepath : str):
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(self.to_serializable(), file, ensure_ascii=False)

    @classmethod
    def from_json(cls, filepath : str):
        with open(filepath, encoding='utf-8') as file:
            return cls.from_serializable(json.load(file))

    @classmethod
    def from_serializable(cls, serializable : dict):
        return cls(**serializable)
    
    def add_token(self, token : str) -> int:
        if token not in self._token_to_idx:
            idx = len(self._token_to_idx)
            self._token_to_idx[token] = idx
            self._idx_to_token[idx] = token
            return idx
        else:
            return self._token_to_idx[token]

    def add_tokens(self, tokens : list[str]) -> list:
        return [self.add_token(token) for token in tokens]

    def get_token_index(self, token : str) -> int:
        if token in self._token_to_idx:
            return self._token_to_idx[token]
        else:
            return self.unk_index

    def get_token(self, index : int) -> str:
        if index in self._idx_to_token:
            return self._idx_to_token[index]
        else:
            return self._unk_token
        
    def size(self):
        return len(self._token_to_idx)

class SeparatorTokenizer:
    '''Simple implementation one of tokenization algorithms'''
    def __init__(self):
        pass

    def tokenize(self, text : str, separator : str = ' ') -> list:
        text = re.sub(r'([^\w\s]|_)', r' \1 ', text)
        return text.split(separator)

class Vectorizer:
    def __init__(self, tokens_vocab : Vocabulary, label_vocab : Vocabulary, max_sentence_len):
        '''max_sentence_len is using by vectorize() specified for CNN'''
        self.tokens_vocab = tokens_vocab
        self.label_vocab = label_vocab
        self.max_sentence_len = max_sentence_len

    def vectorize_vector(self, tokens : list[str], is_target=False) -> np.array:
        '''Returns one hot vector'''
        cw_vocab = self.label_vocab if is_target else self.tokens_vocab
        one_hot = np.zeros(len(cw_vocab), dtype=np.float32)
        for token in tokens:
            one_hot[cw_vocab.get_token_index(token)] = 1
        return one_hot
    
    def vectorize_matrix(self, tokens : list[str], is_target=False) -> np.array:
        '''Returns one hot matrix. Especially for Convolutional NN'''
        one_hot_matrix_size = (len(self.tokens_vocab), self.max_sentence_len)
        one_hot_matrix = np.zeros(one_hot_matrix_size, dtype=np.float32)
        for token_pos, token in enumerate(tokens):
            one_hot_matrix[self.tokens_vocab.get_token_index(token)][token_pos] = 1
        return one_hot_matrix


    @classmethod
    def from_dataframe(cls, texts_df, threshold_freq = 25):
        pass

    @classmethod
    def from_serializable(cls, serializable : dict):
        return Vectorizer(tokens_vocab=\
                          serializable['tokens_vocab'].from_serializable(),
                          label_vocab=\
                          serializable['label_vocab'].from_serializable())
    
    def to_serializable(self) -> dict:
        return {'tokens_vocab' : self.tokens_vocab.to_serializable(), 'label_vocab' : self.label_vocab.to_serializable()}

class CustomDataset:
    def __init__(self, dataframe : pandas.DataFrame, tokenizer, vectorizer : Vectorizer):
        self._vectorizer = vectorizer
        self._tokenizer = tokenizer

        self._main_df = dataframe

        self._train_df = self._main_df[self._main_df.split == 'train']
        self._train_len = len(self._train_df)

        self._valid_df = self._main_df[self._main_df.split == 'validation']
        self._valid_len = len(self._valid_df)

        self._test_df = self._main_df[self._main_df.split == 'test']
        self._test_len = len(self._test_df)

        self._lookup_split = {'train' : (self._train_df, self._train_len),\
                              'validation' : (self._valid_df, self._valid_len),\
                              'test' : (self._test_df, self._test_len)}
        
        self.set_dataframe_split('train')

    def __getitem__(self, index):
        '''data and target collumns must be named 'x_data' and 'y_target'! '''
        row = self._cw_dataframe.iloc[index]
        data = self._vectorizer.vectorize_matrix(self._tokenizer.tokenize(row['x_data']), is_target=False)
        target = self._vectorizer.vectorize_vector(row['y_target'], is_target=True)
        return {'x_data' : data,\
                'y_target' : target}
    
    def __len__(self):
        return self._cw_df_len
    
    def set_dataframe_split(self, split='train'):
        '''Set a current data split. Allowed values: train, test, validation'''
        self._cw_dataframe, self._cw_df_len = self._lookup_split[split]