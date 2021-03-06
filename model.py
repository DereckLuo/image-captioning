import tensorflow as tf
from pretrained.vgg16 import vgg16
import numpy as np
from pretrained.imagenet_classes import class_names

class ImageCaptioner(object):
    def __init__(self, config, word_table):

        self.config = config
        self.word_table = word_table
        # Create session
        self.session = tf.Session()

        # Create architecture
        self.imgs_placeholder = tf.placeholder(tf.float32, [None, 224, 224, 3])
        self.cnn_output = None
        self.build_cnn()
        self.build_rnn()

        self.session.run(tf.global_variables_initializer())
        self.saver = tf.train.Saver(max_to_keep = 100)

        # load shared weights if necessary
        if config.cnn_model_file:
            self.cnn.load_weights(config.cnn_model_file, self.session)


    def build_cnn(self):
        print('Building CNN...')

        if self.config.cnn_model == 'custom':
            self.build_custom_cnn()

        else:
            self.build_vgg16()

    def build_custom_cnn(self):
        print('Building custom model...')

        W_conv1 = _weight_variable([5, 5, 1, 32])
        b_conv1 = _bias_variable([32])
        h_conv1 = tf.nn.relu(_conv2d(imgs_placeholder, W_conv1) + b_conv1)
        h_pool1 = _max_pool_2x2(h_conv1)

        W_conv2 = _weight_variable([5, 5, 32, 64])
        b_conv2 = _bias_variable([64])
        h_conv2 = tf.nn.relu(_conv2d(h_pool1, W_conv2) + b_conv2)
        h_pool2 = _max_pool_2x2(h_conv2)

        W_conv3 = _weight_variable([5, 5, 64, 128])
        b_conv3 = _bias_variable([128])
        h_conv3 = tf.nn.relu(_conv2d(h_pool2, W_conv3) + b_conv3)
        h_pool3 = _max_pool_2x2(h_conv3)
        h_flat3 = tf.reshape(h_pool3, [-1])

        # TODO: Possibly add some FC layers here

        self.cnn_output = h_flat3

    def build_vgg16(self):
        print('Building VGG-16...')
        self.cnn = vgg16(self.imgs_placeholder, sess=self.session, trainable=self.config.train_cnn)
        # self.cnn_output = conv_net.fc2


    def build_rnn(self):
        print('Building RNN...')

        batch_size = self.config.batch_size
        hidden_size = self.config.hidden_size
        learning_rate = self.config.learning_rate
        num_words = self.word_table.num_words
        max_num_words = self.word_table.max_num_words

        feats = self.cnn_output
        sentences = tf.placeholder(tf.int32, [batch_size, max_num_words])
        masks = tf.placeholder(tf.int32, [batch_size, max_num_words])
        
        lstm = tf.nn.rnn_cell.LSTMCell(hidden_size)
        
        state = tf.zeros([self.batch_size, lstm.state_size])

        W_word = tf.Variable(tf.random_uniform([hidden_size, num_words]))
        b_word = tf.Variable(tf.zeros([num_words]))

        total_loss = 0
        
        for idx in range(max_num_words):
            if idx == 0:
                curr_emb = feats
            else:
                curr_emb = tf.nn.embedding_lookup(self.word_table.word2vec, sentences[:,idx-1])
                    
            output, state = lstm(curr_emb, state)

            logit = tf.matmul(output, W_word)+b_word
                
            labels = tf.expand_dims(sentence[:,i], 1)
            indices = tf.expand_dims(tf.range(0,batch_size), 1)
            label_matrix = tf.concat(1, [indices, labels])
            outhot_labels = tf.sparse_to_dense(label_matrix, tf.pack([batch_size, num_words]), 1)
                
            cross_entropy = tf.nn.softmax_cross_entropy_with_logits(logits, onehot_labels)*mask[:,i]
            loss = tf.reduce_sum(cross_entropy)
            total_loss = total_loss + loss
        
        
        self.total_loss = total_loss
        self.train_op = tf.train.AdamOptimizer(self.learning_rate).minimize(total_loss)


    def train(self, train_data):
        print('Training model...')
        if self.config.train_cnn:
            pass
        else:
            self.session.run()

    def test(self, test_data):
        # THIS IS ONLY TESTING CONVNET SO FAR!!!
        print('Testing model...')
        feed_dict = {self.imgs_placeholder: test_data}
        prob = self.session.run(self.cnn.probs, feed_dict=feed_dict)[0]
        preds = (np.argsort(prob)[::-1])[0:5]
        for p in preds:
            print(class_names[p], prob[p])

    # Layers/initializers
    def _conv2d(x, W):
        return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')

    def _weight_variable(shape):
          initial = tf.truncated_normal(shape, stddev=0.1)
          return tf.Variable(initial)

    def _bias_variable(shape):
      initial = tf.constant(0.1, shape=shape)
      return tf.Variable(initial)

    def _max_pool_2x2(x):
          return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
                                strides=[1, 2, 2, 1], padding='SAME')
