"""
Module defining a simple profiling function, 

Copyright (C) 2015 ERT Inc.

"""
import cProfile
import io
import pstats
import contextlib
import sys

__author__ = "Brandon J. Van Vaerenbergh<brandon.vanvaerenbergh@noaa.gov>, "

@contextlib.contextmanager
def print_profile_to_stderr():
    """
    Utility function,to profile code via a 'with' compound statement

    "contextmanager" decorator is used, so we don't need to type out a class or
    separate __enter__() & __exit__() functions. For more info, see:
    https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager

    Usage: To profile execution of one or more Python statements, indent the target
    code inside of a 'with' compound statement as follows:

    myUnprofiledStatement1()
    with api.profile.print_profile_to_stderr():
        myStatement1()
        myStatement2()
    myUnprofiledStatement2()

    Output will look like:
    Ordered by: cumulative time

    ncalls  tottime  percall  cumtime  percall filename:lineno(function)
         n    0.xyz    0.xyz   0.abc   0.abc   {method '?' of '?' objects}
         n    0.wxy    0.wxy   0.bcd   0.bcd   {method '?' of '?' objects}
     ...
    n function calls in 0.abc seconds
    """
    #Upon exection, set up a native-c Python code profiler
    profiler = cProfile.Profile()
    profiler.enable()
    # Yeild a throwaway object,for 'with' statement to bind to its 'as' clause
    yield None
    # The code block nested in the with statement is now executed..
    #... Upon nested code block completion,execution resumes here automatically
    # Halt profiling, collect outcome, + print
    profiler.disable()
    string_stream = io.StringIO()
    profiler_report = pstats.Stats(profiler, stream=string_stream)
    profiler_report.sort_stats('cumulative')
    profiler_report.print_stats()
    # Write outcome, to somewhere mod_wsgi can see+log it.
    sys.stderr.write( string_stream.getvalue() )
