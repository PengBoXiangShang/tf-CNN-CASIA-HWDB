#!/usr/bin/env python
# -*- coding:utf-8 -*-
###################################################
#      Filename: sample_data.py
#        Author: lzw.whu@gmail.com
#       Created: 2017-11-15 22:53:41
# Last Modified: 2017-11-17 09:49:07
###################################################
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import numpy as np
from sklearn.utils import shuffle


def read_from_gnt_dir(gnt_dir):

    def one_file(f):
        header_size = 10
        while True:
            _sample_size = np.fromfile(f, np.dtype('<u4'), 1)
            if not _sample_size.size:
                break
            sample_size = _sample_size[0]
            tagcode = np.fromfile(f, np.dtype('<u2'), 1)[0]
            width = np.fromfile(f, np.dtype('<u2'), 1)[0]
            height = np.fromfile(f, np.dtype('<u2'), 1)[0]
            if header_size + width * height != sample_size:
                break
            img = np.fromfile(f, np.uint8, width * height).reshape((height, width))
            yield tagcode, img

    for fn in os.listdir(gnt_dir):
        if fn.endswith(".gnt"):
            fn = os.path.join(gnt_dir, fn)
            with open(fn, 'rb') as f:
                for tagcode, img in one_file(f):
                    yield tagcode, img


def extract_first_100_images(gnt_dir):
    i = 0
    for tagcode, img in read_from_gnt_dir(gnt_dir):
        try:
            tag = struct.pack('<H', tagcode).decode('gb2312')
            i += 1
        except:
            continue
        print('0x%04x' % tagcode, tag, img.shape)
        png = Image.fromarray(img)
        png.convert('RGB').save('./png/' + tag + str(i) + '.png')
        if i > 100:
            break


def resize_image(img):
    import scipy.misc

    pad_size = abs(img.shape[0] - img.shape[1]) // 2
    if img.shape[0] < img.shape[1]:
        pad_dims = ((pad_size, pad_size), (0, 0))
    else:
        pad_dims = ((0, 0), (pad_size, pad_size))
    img = np.pad(img, pad_dims, mode='constant', constant_values=255)
    img = scipy.misc.imresize(img, (64 - 4 * 2, 64 - 4 * 2))
    img = np.pad(img, ((4, 4), (4, 4)), mode='constant', constant_values=255)
    assert img.shape == (64, 64)

    img = img.flatten()
    return img


def normalize_img(img):
    img = (img - 128) / 128
    return img


def read_data_sets(gnt_bin, batch_size=50, normalize_image=True, tag_in=[], one_hot=True):
    with open(gnt_bin, 'rb') as f:
        if not tag_in:
            tagcode_all = []
            while True:
                buf = np.fromfile(f, np.uint8, 4098)
                if not buf.size:
                    break
                tagcode = np.frombuffer(buf, np.dtype('<u2'), 1)[0]
                if tagcode not in tagcode_all:
                    tagcode_all.append(tagcode)

        f.seek(0, os.SEEK_SET)
        x = []
        y = []
        while True:
            buf = np.fromfile(f, np.uint8, 4098)
            if not buf.size:
                break

            tagcode = np.frombuffer(buf, np.dtype('<u2'), 1)[0]
            if not tag_in:
                if tagcode not in tagcode_all:
                    continue
            elif tagcode not in tag_in:
                continue

            if one_hot:
                if not tag_in:
                    label = np.zeros(len(tagcode_all))
                    label[tagcode_all.index(tagcode)] = 1
                else:
                    label = np.zeros(len(tag_in))
                    label[tag_in.index(tagcode)] = 1
            else:
                label = tagcode

            image = np.frombuffer(buf, np.uint8, 4096)
            if normalize_image:
                image = (image - 128) / 128
            x.append(image)
            y.append(label)
            assert len(x) == len(y)
            if len(x) == batch_size:
                x, y = shuffle(x, y, random_state=0)
                _x = np.array(x[:])
                _y = np.array(y[:])
                x = []
                y = []
                yield _x, _y