#!/usr/bin/env python
# -*- coding:utf-8 -*-
###################################################
#      Filename: train.py
#        Author: lzw.whu@gmail.com
#       Created: 2017-11-15 23:51:22
# Last Modified: 2017-11-21 11:01:58
###################################################
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from six.moves import xrange
from PIL import Image
from struct import pack, unpack
import numpy as np
import os, sys
import argparse
import tensorflow as tf

import sample_data
import model

FLAGS = None

trn_gnt_bin = "/home/aib/datasets/HWDB1.1trn_gnt.bin"
tst_gnt_bin = "/home/aib/datasets/HWDB1.1tst_gnt.bin"
model_path = "/home/aib/models/tf-CNN-CASIA-HWDB/model.ckpt"

learning_rate = 1e-3
epochs = 40
batch_size = 500
batch_size_test = 5000
step_display = 10
step_save = 100
p_keep_prob = 0.5
normalize_image = True
one_hot = True


def main(_):
    if FLAGS.charset == 0:
        char_set = "的一是了我不人在他有这个上们来到时大地为子中你说生国年着就那和要她出也得里后自以会家可下而过天去能对小多然于心学么之都好看起发当没成只如事把还用第样道想作种开美总从无情己面最女但现前些所同日手又行意动方期它头经长儿回位分爱老因很给名法间斯知世什两次使身者被高已亲其进此话常与活正感"
        tag_in = map(lambda x: unpack('<H', x.encode('gb2312'))[0], char_set)
        assert len(char_set) == len(tag_in)
    elif FLAGS.charset == 1:
        tag_in = []

    if not tag_in:
        n_classes = 3755
    else:
        n_classes = len(tag_in)

    x = tf.placeholder(tf.float32, [None, 4096])
    y = tf.placeholder(tf.int32, [None, n_classes])
    keep_prob = tf.placeholder(tf.float32)

    pred = model.CNN(x, n_classes, keep_prob)
    cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=pred, labels=y))
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)

    correct = tf.equal(tf.argmax(pred, 1), tf.argmax(y, 1))
    accuracy = tf.reduce_mean(tf.cast(correct, tf.float32))

    cr5 = tf.reduce_mean(tf.cast(tf.nn.in_top_k(pred, tf.argmax(y, 1), 5), tf.float32))
    cr10 = tf.reduce_mean(tf.cast(tf.nn.in_top_k(pred, tf.argmax(y, 1), 10), tf.float32))

    tf.summary.scalar("loss", cost)
    tf.summary.scalar("accuracy", accuracy)
    merged_summary_op = tf.summary.merge_all()

    saver = tf.train.Saver()
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())

        summary_writer = tf.summary.FileWriter("./log", graph=tf.get_default_graph())

        if FLAGS.action == 'train':
            i = 0
            for epoch in xrange(epochs):
                for batch_x, batch_y in sample_data.read_data_sets(trn_gnt_bin, batch_size=batch_size, normalize_image=normalize_image, tag_in=tag_in, one_hot=one_hot):
                    _, summary = sess.run([optimizer, merged_summary_op], feed_dict={x: batch_x, y: batch_y, keep_prob: p_keep_prob})
                    summary_writer.add_summary(summary, i)
                    i += 1
                    if i % step_display == 0:
                        loss, acc = sess.run([cost, accuracy], feed_dict={x: batch_x, y: batch_y, keep_prob: 1.})
                        print("batch:%s\tloss:%s\taccuracy:%s" % (i, "{:.6f}".format(loss), "{:.5f}".format(acc)))
                    if i % step_save == 0:
                        saver.save(sess, model_path)
            print("training done.")
            saver.save(sess, model_path)
        else:
            saver.restore(sess, model_path)
            print("model restored.")

        i = 0
        sum_cr1 = 0.
        sum_cr5 = 0.
        sum_cr10 = 0.
        for batch_x, batch_y in sample_data.read_data_sets(tst_gnt_bin, batch_size=batch_size, normalize_image=normalize_image, tag_in=tag_in, one_hot=one_hot):
            loss, acc, _cr5, _cr10 = sess.run([cost, accuracy, cr5, cr10], feed_dict={x: batch_x, y: batch_y, keep_prob: 1.})
            print("Loss:{:.6f}\tCR(1):{:.5f}\tCR(5):{:.5f}\tCR(10):{:.5f}".format(loss, acc, _cr5, _cr10))
            sum_cr1 += acc
            sum_cr5 += _cr5
            sum_cr10 += _cr10
            i += 1
        print("============================================================")
        print("CR(1):{:.5f}\tCR(5):{:.5f}\tCR(10):{:.5f}".format(sum_cr1 / i, sum_cr5 / i, sum_cr10 / i))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', type=str, help='[train|inference]')
    parser.add_argument('charset', type=int, help='0:only mostly used 140 characters; 1:3755 characters in GB2312')
    FLAGS, unparsed = parser.parse_known_args()
    tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)