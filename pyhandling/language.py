from functools import partial
from typing import Callable, Optional, Iterable, Any, Self

from pyannotating import Special

from pyhandling.binders import post_partial
from pyhandling.branchers import ActionChain
from pyhandling.tools import DelegatingProperty, documenting_by




then = documenting_by(
    """
    Neutral instance of the ActionChain class.

    Used as an operator emulator for convenient construction of ActionChains.
    Assumes usage like \"first_handler |then>> second_handler\".

    Additional you can add any resource to the beginning of the construction
    and >= after it to call the constructed chain with this resource.

    You get something like this \"resource >= first_handler |then>> second_handler\".

    See ActionChain for more info.
    """
)(
    ActionChain()
)
