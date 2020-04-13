"""
Decoders and output normalization for CTC

Author:
    Mirco Ravanelli, Aku Rouhe 2020
"""
import torch
from itertools import groupby


def filter_ctc_output(string_pred, blank_id=-1):
    """Apply CTC output merge and filter rules.
    
    Removes the blank symbol and output repetitions. 

    Parameters
    ---------- 
    string_pred : list
        a list containing the output strings/ints predicted by the CTC system
    blank_id : int, string
        the id of the blank

    Returns 
    ------
    list
          The output predicted by CTC without the blank symbol and 
          the repetitions

    Example
    -------
        >>> string_pred = ['a','a','blank','b','b','blank','c']
        >>> string_out = filter_ctc_output(string_pred, blank_id='blank')
        >>> print(string_out)
        ['a', 'b', 'c']

    Author
    ------
        Mirco Ravanelli 2020
    """

    if isinstance(string_pred, list):
        # Filter the repetitions
        string_out = [
            v
            for i, v in enumerate(string_pred)
            if i == 0 or v != string_pred[i - 1]
        ]

        # Remove duplicates
        string_out = [i[0] for i in groupby(string_out)]

        # Filter the blank symbol
        string_out = list(filter(lambda elem: elem != blank_id, string_out))
    else:
        raise ValueError("filter_ctc_out can only filter python lists")
    return string_out


def ctc_greedy_decode(probabilities, seq_lens, blank_id):
    """
    Greedy decode a batch of probabilities and apply CTC rules

    Parameters
    ----------
    probabilities : torch.tensor
        Output probabilities (or log-probabilities) from network
    seq_lens : torch.tensor
        Relative true sequence lengths (to deal with padded inputs),
        longest sequence has length 1.0, others a value betwee zero and one
    blank_id : int, string
        The blank symbol

    Returns
    -------
    list
        Outputs as Python list of lists, with "ragged" dimensions; padding
        has been removed.

    Example
    -------
        >>> import torch
        >>> probs = torch.tensor([[[0.3, 0.7], [0.0, 0.0]],
        ...                       [[0.2, 0.8], [0.9, 0.1]]]).transpose(2,1)
        >>> lens = torch.tensor([0.51, 1.0])
        >>> blank_id = 0
        >>> ctc_greedy_decode(probs, lens, blank_id)
        [[1], [1]]
    
    Author:
        Aku Rouhe 2020
    """
    batch_max_len = probabilities.shape[-1]  # Assume time last
    batch_outputs = []
    for seq, seq_len in zip(probabilities, seq_lens):
        actual_size = int(
            torch.round(seq_len * batch_max_len)
        )
        scores, predictions = torch.max(seq.narrow(-1, 0, actual_size), dim=0)
        out = filter_ctc_output(
                predictions.tolist(), blank_id=blank_id
        )
        batch_outputs.append(out)
    return batch_outputs
