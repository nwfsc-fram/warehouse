"""
Module defining utility functions for Selection HTTP chunked encoding

HTTP chunked encoding improves responsiveness, by enabling API to begin
  sending initial data to the client before the Selection has been
  completely retrieved.
"""

def biggerchunks_stream(generator, multiplier=2):
    """
    Returns a String generator wrapper, which increases the length of
      yielded incremental Strings by concatenating them together.

    Keyword Parameters:
    generator  -- generator, yielding the initial input chunks
    multiplier -- int, representing how much bigger output chunks
      should be

    >>> # Check muliplier=1 (i.e.: no change)
    >>> start_generator = ('a' for i in range(2))
    >>> test = biggerchunks_stream(start_generator, multiplier=1)
    >>> test.__next__()
    'a'
    >>> test.__next__()
    'a'
    >>> test.__next__()
    Traceback (most recent call last):
       ...
    StopIteration
    >>> # Check muliplier=2
    >>> start_generator = ('a' for i in range(4))
    >>> test = biggerchunks_stream(start_generator) #x2 is the default
    >>> test.__next__()
    'aa'
    >>> test.__next__()
    'aa'
    >>> test.__next__()
    Traceback (most recent call last):
       ...
    StopIteration
    >>> # Check generator that doesnt return an even multiplier multiple
    >>> start_generator = ('a' for i in range(7))
    >>> test = biggerchunks_stream(start_generator, multiplier=3)
    >>> test.__next__()
    'aaa'
    >>> test.__next__()
    'aaa'
    >>> test.__next__()
    'a'
    >>> test.__next__()
    Traceback (most recent call last):
       ...
    StopIteration
    """
    while True: #continue running until input generator is exhausted
        batch = None
        # String, representing concatinated input chunks
        for batch_index in range(multiplier):
            try:
                one_item = next(generator)
            except StopIteration as generator_exhausted:
                if batch is None:
                    # nothing to do: just pass along the status
                    raise generator_exhausted
                yield batch # conceal the exception & return partial batch
                # Now, upon next call immediately raise StopIteration
                raise StopIteration() from generator_exhausted
            # add generator output to the batch
            if batch is not None:
                batch += one_item
            else: # batch was None: start a new batch
                batch = one_item
        else:
            yield batch #full batch complete, next call starts new batch
