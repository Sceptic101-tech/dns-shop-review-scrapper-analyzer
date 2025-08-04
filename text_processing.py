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
    def __init__(self, token_to_idx : dict = None, mask_token : str = '<MASK>', unk_token : str = '<UNK>',\
                 bos_token : str = 'BOS', eos_token : str = 'EOS', is_lexical_tokens=True):
        if token_to_idx is None:
            token_to_idx = {}
        self._token_to_idx = token_to_idx
        self._idx_to_token = {value : key for key, value in token_to_idx.items()}

        self._is_lexical_tokens = is_lexical_tokens
        self.mask_token = mask_token
        self._unk_token = unk_token
        self._bos_token = bos_token
        self._eos_token = eos_token

        if is_lexical_tokens:
            self.mask_token_index = self.add_token(mask_token)
            self.unk_index = self.add_token(self._unk_token)
            self._bos_index = self.add_token(self._bos_token)
            self._eos_index = self.add_token(self._eos_token)

    def __len__(self) -> int:
        return len(self._token_to_idx)

    def to_serializable(self) -> dict: # переделать
        return {'token_to_idx' : self._token_to_idx, 'mask_token' : self.mask_token,\
                'unk_token' : self._unk_token, 'bos_token' : self._bos_token, 'eos_token' : self._eos_token, 'is_lexical_tokens' : self._is_lexical_tokens}
    
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

    @classmethod
    def from_dataframe(cls, dataframe : pandas.DataFrame, tokenizer, treshold_freq=25):
        pass
    
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
        text = re.sub(r'([^\w\s]|_)', r' \1 ', text) # Отделяем пробелом знаки препинаня, они будут считаться отдельным токеном
        text = re.sub(r'[\t\n\r\f\v]', r' ', text)
        return text.split(separator)

class Vectorizer:
    def __init__(self, tokens_vocab : Vocabulary, label_vocab : Vocabulary, max_sentence_len : int):
        '''max_sentence_len is using by vectorize() specified for CNN'''
        self.tokens_vocab = tokens_vocab
        self.label_vocab = label_vocab
        self.max_sentence_len = max_sentence_len

    def vectorize_vector_onehot(self, tokens : list[str], is_target=False) -> np.array:
        '''Returns one hot vector'''
        cw_vocab = self.label_vocab if is_target else self.tokens_vocab
        one_hot = np.zeros(len(cw_vocab), dtype=np.float32)
        for token in tokens:
            one_hot[cw_vocab.get_token_index(token)] = 1
        return one_hot
    
    def vectorize_matrix_onehot(self, tokens : list[str]) -> np.array:
        '''Returns one hot matrix. Especially for Convolutional NN'''
        one_hot_matrix_size = (len(self.tokens_vocab), self.max_sentence_len)
        one_hot_matrix = np.zeros(one_hot_matrix_size, dtype=np.float32)
        for token_pos, token in enumerate(tokens):
            one_hot_matrix[self.tokens_vocab.get_token_index(token)][token_pos] = 1
        return one_hot_matrix
    
    def vectorize_vector_indices(self, tokens : list[str]):
        '''Returns list of tokens indices. Use for Embedding layer as input'''
        indices = [self.tokens_vocab._bos_index]
        for token in tokens:
            indices.append(self.tokens_vocab.get_token_index(token))
        indices.append(self.tokens_vocab._eos_index)

        final_vec = np.zeros(self.max_sentence_len, dtype=np.int64)
        final_vec[:len(indices)] = indices
        final_vec[len(indices):] = self.tokens_vocab.mask_token_index
        
        return final_vec, len(indices)
    
    def vectorize_vectors_indices(self, tokens : list[str]) -> tuple[list, list, int]:
        '''Use for sequence prediction.\
        Returns two vectors and useful length(len without masking): \
        **from_vector**(inputs for RNN at each timestamp)\
        **to_vector**(expexted ouputs of RNNCell at each timestamp)'''

        indices = [self.tokens_vocab._bos_index]
        for token in tokens:
            indices.append(self.tokens_vocab.get_token_index(token))
        indices.append(self.tokens_vocab._eos_index)

        from_vector = np.empty(self.max_sentence_len, dtype=np.int64)
        from_indices = indices[:-1] # everything except last element
        from_vector[:len(from_indices)] = from_indices
        from_vector[len(from_indices):] = self.tokens_vocab.mask_token_index

        to_vector = np.empty(self.max_sentence_len, dtype=np.int64)
        to_indices = indices[1:] # everything except first element
        to_vector[:len(from_indices)] = to_indices
        to_vector[len(from_indices):] = self.tokens_vocab.mask_token_index
        
        return from_vector, to_vector, len(from_indices)


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
        '''data and target collumns must be named 'x_data' and 'y_target'!\
            Use current realisation for Embed and RNN text generation'''
        row = self._cw_dataframe.iloc[index]
        from_vec, to_vec, useful_len = self._vectorizer.vectorize_vectors_indices(self._tokenizer.tokenize(row['x_data']))
        label = self._vectorizer.vectorize_vector_onehot(row['y_target'], is_target=True)
        return {'x_data' : from_vec,\
                'y_target' : to_vec,
                'label' : label,
                'useful_len' : useful_len}
    
    def __len__(self):
        return self._cw_df_len
    
    def set_dataframe_split(self, split='train'):
        '''Set a current data split. Allowed values: train, test, validation'''
        self._cw_dataframe, self._cw_df_len = self._lookup_split[split]