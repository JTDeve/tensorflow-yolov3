#! /usr/bin/env python
# coding=utf-8
#================================================================
#   Copyright (C) 2018 * Ltd. All rights reserved.
#
#   Editor      : VIM
#   File name   : train.py
#   Author      : YunYang1994
#   Created date: 2018-11-30 15:47:45
#   Description :
#
#================================================================


import tensorflow as tf
from core import utils, yolov3

INPUT_SIZE = 416
BATCH_SIZE = 1
EPOCHS = 700000
LR = 0.0001
SHUFFLE_SIZE = 1

sess = tf.Session()
# classes = utils.read_coco_names('./data/coco.names')
num_classes = 20
# file_pattern = "../COCO/tfrecords/coco*.tfrecords"
file_pattern = "/home/yang/test/voc/voc_train*.tfrecords"
# file_pattern = "/home/yang/test/kangaroo/tfrecords/kangaroo*.tfrecords"
# file_pattern = "./data/train_data/quick_train_data/tfrecords/quick_train_data*.tfrecords"
anchors = utils.get_anchors('./data/yolo_anchors.txt')

is_training = tf.placeholder(dtype=tf.bool, name="phase_train")
dataset = tf.data.TFRecordDataset(filenames = tf.gfile.Glob(file_pattern))
dataset = dataset.map(utils.parser(anchors, num_classes).parser_example, num_parallel_calls = 10)
dataset = dataset.repeat().shuffle(SHUFFLE_SIZE).batch(BATCH_SIZE).prefetch(BATCH_SIZE)
iterator = dataset.make_one_shot_iterator()
example = iterator.get_next()

images, *y_true = example
model = yolov3.yolov3(num_classes)
with tf.variable_scope('yolov3'):
    y_pred = model.forward(images, is_training=is_training)
    loss = model.compute_loss(y_pred, y_true)
    y_pred = model.predict(y_pred)


optimizer = tf.train.MomentumOptimizer(LR, momentum=0.9)
saver = tf.train.Saver(max_to_keep=2)

update_var = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope="yolov3/yolo-v3")
train_op = optimizer.minimize(loss[0], var_list=update_var) # only update yolo layer
sess.run(tf.global_variables_initializer())

pretrained_weights = tf.global_variables(scope="yolov3/darknet-53")
load_op = utils.load_weights(var_list=pretrained_weights,
                            weights_file="../darknet53.conv.74")
sess.run(load_op)


for epoch in range(EPOCHS):
    run_items = sess.run([train_op] + loss, feed_dict={is_training:True})
    if epoch%1000 == 0: saver.save(sess, save_path="./checkpoint/yolov3.ckpt", global_step=epoch)

    print("=> EPOCH:%10d\ttotal_loss:%7.4f\tloss_coord:%7.4f\tloss_sizes:%7.4f\tloss_confs:%7.4f\tloss_class:%7.4f"
          %(epoch, run_items[1], run_items[2], run_items[3], run_items[4], run_items[5]))







