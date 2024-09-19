# SPDX-FileCopyrightText: 2018 Stanford Intelligent Systems Laboratory
#
# SPDX-License-Identifier: MIT
"""Write a NNet.

The file was adapted from <https://github.com/sisl/NNet>.
The original file was licensed under MIT License.
The original license is included below.

The MIT License (MIT)

Copyright (c) 2018 Stanford Intelligent Systems Laboratory

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def write_nnet(
    weights, biases, input_mins, input_maxes, means, ranges, file_name
):  # pylint: disable=too-many-arguments, too-many-locals
    """Write network data to the .nnet file format.

    Args:
        weights (list): Weight matrices in the network order
        biases (list): Bias vectors in the network order
        inputMins (list): Minimum values for each input
        inputMaxes (list): Maximum values for each input
        means (list): Mean values for each input and a mean value for
            all outputs. Used to normalize inputs/outputs
        ranges (list): Range values for each input and a range value for
            all outputs. Used to normalize inputs/outputs
        fileName (str): File where the network will be written
    """

    # Open the file we wish to write
    with open(file_name, "w", encoding="utf-8") as f2:
        """Writing the file will follow this pattern:

        First, we write the header lines:
        The first line written is just a line of text
        The second line gives the four values:
            Number of fully connected layers in the network
            Number of inputs to the network
            Number of outputs from the network
            Maximum size of any hidden layer
        The third line gives the sizes of each layer, including the
            input and output layers
        The fourth line gives an outdated flag, so this can be ignored
        The fifth line specifies the minimum values each input can take
        The sixth line specifies the maximum values each input can take
            Inputs passed to the network are truncated to be between this range
        The seventh line gives the mean value of each input and of all outputs
        The eighth line gives the range of each input and of all outputs
            These two lines are used to map raw inputs to the 0 mean,
            unit range of the inputs and outputs
            used during training
        The ninth line begins the network weights and biases
        """
        f2.write("// Neural Network File Format by Kyle Julian, Stanford 2016\n")

        # Extract the necessary information and write the header information
        num_layers = len(weights)
        input_size = weights[0].shape[1]
        output_size = len(biases[-1])
        max_layer_size = input_size

        # Find maximum size of any hidden layer
        for b in biases:
            if len(b) > max_layer_size:
                max_layer_size = len(b)

        # Write data to header
        f2.write(f"{num_layers:d},{input_size:d},{output_size:d},{max_layer_size:d},\n")
        f2.write(f"{input_size:d},")
        for b in biases:
            f2.write(f"{len(b):d},")
        f2.write("\n")
        f2.write("0,\n")  # Unused Flag

        # Write Min, Max, Mean, and Range of each of the inputs and
        # outputs for normalization
        f2.write(
            ",".join(str(input_mins[i]) for i in range(input_size)) + ",\n"
        )  # Minimum Input Values
        f2.write(
            ",".join(str(input_maxes[i]) for i in range(input_size)) + ",\n"
        )  # Maximum Input Values
        f2.write(
            ",".join(str(means[i]) for i in range(input_size + 1)) + ",\n"
        )  # Means for normalizations
        f2.write(
            ",".join(str(ranges[i]) for i in range(input_size + 1)) + ",\n"
        )  # Ranges for normalizations

        ##################
        # Write weights and biases of neural network
        # First, the weights from the input layer to the first hidden
        # layer are written.
        # Then, the biases of the first hidden layer are written
        # The pattern is repeated by next writing the weights from the
        # first hidden layer to the second hidden layer, followed by the
        # biases of the second hidden layer.
        ##################
        for w, b in zip(weights, biases):
            for i in range(w.shape[0]):
                for j in range(w.shape[1]):
                    # Five digits written. More can be used, but require more space.
                    f2.write(f"{w[i][j]:.5e},")
                f2.write("\n")

            for i in range(len(b)):  # pylint: disable=consider-using-enumerate
                # Five digits written. More can be used, but require more space.
                f2.write(f"{b[i]:.5e},\n")
