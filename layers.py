import numpy as np
from helpers import load_mnist_train
from losses import cross_entropy, cross_entropy_prime


class Layer:
    def __init__(self, name):
        self.name = name

    def forward(self, input: np.ndarray):
        self.input = input

    def backward(self, output_gradient: np.ndarray, learning_rate: float):
        pass


class Dense(Layer):
    """
    Fully Connected Layer of Neurons
    """
    def __init__(self, input_size, output_size, name="Dense"):
        self.weights = np.random.uniform(-1, 1, (output_size, input_size))
        self.bias = np.zeros((output_size, 1))
        super().__init__(name)
    def forward(self, input: np.ndarray):
        self.input = input
        return np.dot(self.weights, input) + self.bias
    
    def backward(self, output_gradient: np.ndarray, learning_rate: float):
        grad_weights = output_gradient @ self.input.T
        grad_bias = output_gradient
        self.weights -= learning_rate * grad_weights
        self.bias -= learning_rate * grad_bias
        return self.weights.T @ output_gradient # return the derivative of the loss with respect to inputs


class Activation(Layer):
    """
    Activation function
    """
    def __init__(self, activation, activation_prime, name):
        self.activation = activation
        self.activation_prime = activation_prime
        self.name = name

    def forward(self, input: np.ndarray):
        self.input = input
        return self.activation(input)


class ReLU(Activation):
    """
    ReLU activation.
    Defined as max(x, 0).
    """
    def __init__(self, name):
        relu = lambda x: np.maximum(x, 0)
        relu_prime = lambda x: x > 0
        super().__init__(relu, relu_prime, name)

    def backward(self, output_gradient: np.ndarray, learning_rate: float):
        return output_gradient  * self.activation_prime(self.input)


class Softmax(Activation):
    """
    Softmax activation.
    Converts outputs to probability distribution.
    """
    def __init__(self, name):
        def softmax(x: np.ndarray):
            x = x - np.max(x) # this is to avoid high values (it doesn't change the outputs)
            e = np.exp(x)
            s = e / np.sum(e)
            s = s + 1e-9 # make sure there are no zeros
            return s

        def softmax_prime(x: np.ndarray):
            """
            Calculate Jacobian matrix for Softmax (all partial derivatives with respect to all inputs)
            """
            s = softmax(x).flatten()
            n = len(x)
            jac = np.zeros((n, n))
            for i in range(n):
                for j in range(n):
                    if i == j:
                        jac[i][j] = s[i] * (1 - s[i])
                    else:
                        jac[i][j] = (-1) * s[i] * s[j]
            return jac

        super().__init__(softmax, softmax_prime, name)

    def backward(self, output_gradient: np.ndarray, learning_rate: float):
        """
        The derivative of the softmax function is a Jacobian matrix.
        To calculate the derivative of the loss with respect to the inputs of the softmax, matrix multiply the Jacobian (derivative of the Softmax) with the derivative of the Cross entropy loss with respect to the outputs of the network.
        This result should be the same as (y_pred - y_true)
        """
        return self.activation_prime(self.input).T @ output_gradient


def softmax(x: np.ndarray):
    # x = x - np.max(x) # this is to avoid high values (it doesn't change the outputs)
    e = np.exp(x)
    s = e / np.sum(e)
    return s

if __name__ == "__main__":
    layers = [
        Dense(784, 16, "Input Dense"), # input = (784, 1) | output = (16, 1)
        ReLU("Relu"), # input = (16, 1) | output = (16, 1)
        Dense(16, 10, "Hidden Dense"), # input = (16, 1) | output = (10, 1)
    ]

    # load data
    labels, mnist = load_mnist_train()
    n = len(mnist)

    # transform data
    mnist = mnist.T / 255
    labels = np.eye(len(np.unique(labels)))[labels].T

    epochs = 10

    for e in range(epochs):

        # print(f"Epoch {e}")

        total_loss = 0

        for i in range(n):

            # get sample
            X = mnist[:, i:i+1]
            y = labels[:, i:i+1]

            # forward prop
            output = X
            for layer in layers:
                output = layer.forward(output)
            
            # softmax
            y_pred = softmax(output)
            print(np.sum(y_pred))

            # calculate loss
            loss = cross_entropy(y_pred, y)
            # print(loss)

            # back prop
            grad = y_pred - y # derivative of the loss with respect to outputs of last dense layer
            learning_rate = 0.01

            for layer in layers[::-1]:
                grad = layer.backward(grad, learning_rate)

        # print(f"Epoch Avg loss: {total_loss/n}")