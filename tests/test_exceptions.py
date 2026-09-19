"""
Tests for attrs classes that inherit from BaseException (auto_exc).
"""

from __future__ import absolute_import, division, print_function

import copy
import pickle

import pytest

import attr

from attr.exceptions import FrozenInstanceError


@attr.s(auto_exc=True)
class SimpleError(Exception):
    x = attr.ib()


@attr.s(auto_exc=True)
class TwoAttrsError(Exception):
    x = attr.ib()
    y = attr.ib()


@attr.s(auto_exc=True)
class DefaultError(Exception):
    x = attr.ib()
    y = attr.ib(default=42)
    hidden = attr.ib(init=False, default="h")
    items = attr.ib(init=False, factory=list)


@attr.s(auto_exc=True, slots=True)
class DefaultErrorSlots(DefaultError):
    pass


@attr.s(auto_exc=True, frozen=True)
class DefaultErrorFrozen(DefaultError):
    pass


@attr.s(auto_exc=True, slots=True, frozen=True)
class DefaultErrorSlotsFrozen(DefaultError):
    pass


@attr.s(auto_exc=True)
class FactoryError(Exception):
    x = attr.ib()
    items = attr.ib(factory=list)


@attr.s(auto_exc=True, slots=True)
class FactoryErrorSlots(FactoryError):
    pass


@attr.s(auto_exc=True, frozen=True)
class FactoryErrorFrozen(FactoryError):
    pass


@attr.s(auto_exc=True, slots=True, frozen=True)
class FactoryErrorSlotsFrozen(FactoryError):
    pass


@attr.s(auto_exc=True, kw_only=True)
class KwOnlyError(Exception):
    x = attr.ib()
    y = attr.ib()


@attr.s(auto_exc=True, slots=True, kw_only=True)
class KwOnlyErrorSlots(KwOnlyError):
    pass


@attr.s(auto_exc=True, frozen=True, kw_only=True)
class KwOnlyErrorFrozen(KwOnlyError):
    pass


@attr.s(auto_exc=True, slots=True, frozen=True, kw_only=True)
class KwOnlyErrorSlotsFrozen(KwOnlyError):
    pass


@attr.s(auto_exc=True)
class MixedKwOnlyError(Exception):
    x = attr.ib()
    y = attr.ib(default=9, kw_only=True)


@attr.s(auto_exc=True, slots=True)
class MixedKwOnlyErrorSlots(MixedKwOnlyError):
    pass


@attr.s(auto_exc=True, frozen=True)
class MixedKwOnlyErrorFrozen(MixedKwOnlyError):
    pass


@attr.s(auto_exc=True, slots=True, frozen=True)
class MixedKwOnlyErrorSlotsFrozen(MixedKwOnlyError):
    pass


@attr.s(auto_exc=True)
class InheritanceBaseError(Exception):
    x = attr.ib()


@attr.s(auto_exc=True)
class PostInitError(Exception):
    x = attr.ib()

    def __attrs_post_init__(self):
        self.extra = self.x + 1


@attr.s(auto_exc=True)
class InheritanceMidError(InheritanceBaseError):
    y = attr.ib()


@attr.s(auto_exc=True)
class InheritanceLeafError(InheritanceMidError):
    z = attr.ib()
    w = attr.ib(kw_only=True, default=0)


@attr.s(auto_exc=True, slots=True)
class InheritanceLeafSlotsError(InheritanceMidError):
    z = attr.ib()
    w = attr.ib(kw_only=True, default=0)


DEFAULT_CLASSES = [
    DefaultError,
    DefaultErrorSlots,
    DefaultErrorFrozen,
    DefaultErrorSlotsFrozen,
]
FACTORY_CLASSES = [
    FactoryError,
    FactoryErrorSlots,
    FactoryErrorFrozen,
    FactoryErrorSlotsFrozen,
]
KW_ONLY_CLASSES = [
    KwOnlyError,
    KwOnlyErrorSlots,
    KwOnlyErrorFrozen,
    KwOnlyErrorSlotsFrozen,
]
MIXED_KW_ONLY_CLASSES = [
    MixedKwOnlyError,
    MixedKwOnlyErrorSlots,
    MixedKwOnlyErrorFrozen,
    MixedKwOnlyErrorSlotsFrozen,
]


class TestAutoExc(object):
    """
    General behavior of auto_exc classes.
    """

    def test_basic(self):
        """
        Values end up on both, the attributes and ``args``.
        """
        e = SimpleError(42)

        assert e.x == 42
        assert e.args == (42,)

    def test_make_class(self):
        """
        attr.make_class works with exception bases.
        """
        cls = attr.make_class(
            "MadeError",
            {"x": attr.ib()},
            bases=(Exception,),
            auto_exc=True,
        )

        assert cls(1).args == (1,)
        assert cls(1).x == 1

    @pytest.mark.parametrize("slots", [True, False])
    @pytest.mark.parametrize("frozen", [True, False])
    def test_str_and_repr(self, slots, frozen):
        """
        __str__ and __repr__ behave like those of regular exceptions.
        """

        @attr.s(auto_exc=True, slots=slots, frozen=frozen)
        class E(Exception):
            x = attr.ib()
            y = attr.ib(init=False, default=42)

        e = E(1)

        assert str(e) == "1"
        assert repr(e) == "E(1)"
        assert e.args == (1,)

    def test_str_multiple_args(self):
        """
        Multiple positional values render like a tuple.
        """
        e = TwoAttrsError(1, "foo")

        assert str(e) == "(1, 'foo')"
        assert repr(e) == "TwoAttrsError(1, 'foo')"

    def test_str_is_ignored(self):
        """
        Passing str=True has no effect for auto_exc classes.
        """

        @attr.s(auto_exc=True, str=True)
        class E(Exception):
            x = attr.ib()

        assert str(E("boom")) == "boom"

    @pytest.mark.parametrize("slots", [True, False])
    @pytest.mark.parametrize("frozen", [True, False])
    def test_raise_and_catch(self, slots, frozen):
        """
        Instances can be raised and caught and carry a traceback.
        """

        @attr.s(auto_exc=True, slots=slots, frozen=frozen)
        class MyError(Exception):
            x = attr.ib()

        with pytest.raises(MyError) as ei:
            raise MyError(5)

        e = ei.value
        assert e.x == 5
        assert e.args == (5,)
        assert e.__traceback__ is not None
        assert isinstance(e, Exception)
        assert isinstance(e, BaseException)

    def test_catch_as_base_exception(self):
        """
        Classes can subclass BaseException directly.
        """

        @attr.s(auto_exc=True)
        class ExitLike(BaseException):
            code = attr.ib()

        with pytest.raises(BaseException):
            raise ExitLike(7)

        assert not issubclass(ExitLike, Exception)

    @pytest.mark.parametrize("slots", [True, False])
    def test_identity_equality_and_hashing(self, slots):
        """
        Instances compare and hash by identity like regular exceptions.
        """

        @attr.s(auto_exc=True, slots=slots)
        class E(Exception):
            x = attr.ib()

        assert E(1) != E(1)
        e = E(1)
        assert e == e
        assert hash(e) == hash(e)
        assert {e: 1}[e] == 1

    def test_field_named_args_rejected(self):
        """
        A field called args is rejected to protect the exception
        machinery.
        """
        with pytest.raises(ValueError, match="args"):

            @attr.s(auto_exc=True)
            class E(Exception):
                args = attr.ib()

        with pytest.raises(ValueError, match="args"):
            attr.make_class(
                "E2",
                {"args": attr.ib()},
                bases=(Exception,),
                auto_exc=True,
            )

    def test_custom_init_conflict(self):
        """
        A hand-written __init__ leads to a ValueError.
        """
        with pytest.raises(ValueError, match="__init__"):

            @attr.s(auto_exc=True)
            class E(Exception):
                x = attr.ib()

                def __init__(self, x):
                    self.x = x

    def test_custom_init_with_init_false(self):
        """
        init=False lets users keep their own __init__.
        """

        @attr.s(auto_exc=True, init=False)
        class E(Exception):
            x = attr.ib(init=False)

            def __init__(self, x):
                BaseException.__init__(self, x)
                self.x = x

        assert E(3).args == (3,)
        assert E(3).x == 3

    def test_inherited_init_allowed(self):
        """
        An __init__ inherited from a base class doesn't trigger the
        conflict check.
        """

        class P(Exception):
            def __init__(self, x):
                BaseException.__init__(self, x)
                self.tag = "p"

        @attr.s(auto_exc=True, init=False)
        class E(P):
            y = attr.ib(init=False, default=1)

        assert E(2).tag == "p"

    def test_auto_exc_ignored_for_regular_classes(self):
        """
        auto_exc=True on a non-exception class is a no-op.
        """

        @attr.s(auto_exc=True)
        class Plain(object):
            x = attr.ib()

        assert repr(Plain(1)) == "Plain(x=1)"
        assert Plain(1) == Plain(1)

    @pytest.mark.parametrize("slots", [True, False])
    def test_weakreference(self, slots):
        """
        Slotted exception classes remain weak-referenceable.
        """
        import weakref

        @attr.s(auto_exc=True, slots=slots, weakref_slot=True)
        class E(Exception):
            x = attr.ib()

        e = E(1)
        ref = weakref.ref(e)

        assert ref() is e


class TestArgsContents(object):
    """
    What ends up in ``args`` and what doesn't.
    """

    def test_only_init_attrs(self):
        """
        init=False attributes never end up in args.
        """
        e = DefaultError(1)

        assert e.args == (1, 42)
        assert e.hidden == "h"

    def test_static_defaults_become_part_of_args(self):
        """
        Omitted positional attributes with a static default are included.
        """

        @attr.s(auto_exc=True)
        class E(Exception):
            x = attr.ib()
            y = attr.ib(default=2)

        assert E(1).args == (1, 2)
        assert E(1, 3).args == (1, 3)

    def test_unused_factory_not_in_args(self):
        """
        Factory defaults that were not passed are not part of args.
        """
        e = FactoryError(1)

        assert e.args == (1,)
        assert e.items == []

    def test_passed_factory_value_in_args(self):
        """
        Explicitly passed values for factory attributes are part of args.
        """
        e = FactoryError(1, [2, 3])

        assert e.args == (1, [2, 3])

    def test_takes_self_factory_not_in_args(self):
        """
        takes_self factories are internal and never leak into args.
        """

        @attr.s(auto_exc=True)
        class E(Exception):
            x = attr.ib()
            doubled = attr.ib(
                default=attr.Factory(lambda self: self.x * 2, takes_self=True)
            )

        e = E(21)

        assert e.doubled == 42
        assert e.args == (21,)

    def test_kw_only_not_in_args(self):
        """
        Keyword-only attributes never end up in args.
        """
        assert MixedKwOnlyError(1).args == (1,)
        assert MixedKwOnlyError(1, y=3).args == (1,)

    def test_global_kw_only_empty_args(self):
        """
        With global kw_only, args is always empty.
        """
        assert KwOnlyError(x=1, y=2).args == ()

    def test_converted_value_in_args(self):
        """
        The converted (stored) value ends up in args.
        """

        @attr.s(auto_exc=True)
        class E(Exception):
            n = attr.ib(converter=int)

        e = E("42")

        assert e.n == 42
        assert e.args == (42,)

    def test_leading_underscore_attr_name(self):
        """
        Attributes with leading underscores are still positional in args.
        """

        @attr.s(auto_exc=True)
        class E(Exception):
            _x = attr.ib()

        assert E(4).args == (4,)


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
class TestPickleProtocols(object):
    @pytest.mark.parametrize("cls", DEFAULT_CLASSES)
    def test_pickle_defaults(self, cls, protocol):
        """
        Static defaults and init=False fields round-trip.
        """
        e = cls(1)
        e2 = pickle.loads(pickle.dumps(e, protocol))

        assert type(e2) is cls
        assert e2.args == (1, 42)
        assert e2.x == 1
        assert e2.y == 42
        assert e2.hidden == "h"
        assert e2.items == []

    @pytest.mark.parametrize("cls", FACTORY_CLASSES)
    def test_pickle_factory_omitted(self, cls, protocol):
        """
        An omitted factory value is regenerated from the stored field.
        """
        e2 = pickle.loads(pickle.dumps(cls(1), protocol))

        assert e2.args == (1,)
        assert e2.items == []

    @pytest.mark.parametrize("cls", FACTORY_CLASSES)
    def test_pickle_factory_supplied(self, cls, protocol):
        """
        A supplied factory value round-trips.
        """
        e2 = pickle.loads(pickle.dumps(cls(1, [2]), protocol))

        assert e2.args == (1, [2])
        assert e2.items == [2]

    @pytest.mark.parametrize("cls", KW_ONLY_CLASSES)
    def test_pickle_required_kw_only(self, cls, protocol):
        """
        Required keyword-only attributes can be pickled -- which native
        exceptions do not support.
        """
        e = cls(x=1, y=2)
        e2 = pickle.loads(pickle.dumps(e, protocol))

        assert e2.args == ()
        assert e2.x == 1
        assert e2.y == 2

    @pytest.mark.parametrize("cls", MIXED_KW_ONLY_CLASSES)
    def test_pickle_mixed_kw_only_omitted(self, cls, protocol):
        """
        Optional keyword-only attributes restore their default when
        omitted.
        """
        e2 = pickle.loads(pickle.dumps(cls(1), protocol))

        assert e2.args == (1,)
        assert e2.x == 1
        assert e2.y == 9

    @pytest.mark.parametrize("cls", MIXED_KW_ONLY_CLASSES)
    def test_pickle_mixed_kw_only_supplied(self, cls, protocol):
        """
        Supplied keyword-only attributes round-trip.
        """
        e2 = pickle.loads(pickle.dumps(cls(1, y=3), protocol))

        assert e2.args == (1,)
        assert e2.x == 1
        assert e2.y == 3

    @pytest.mark.parametrize(
        "cls",
        [InheritanceLeafError, InheritanceLeafSlotsError],
    )
    def test_pickle_inheritance(self, cls, protocol):
        """
        Multi-level hierarchies pickle, including keyword-only fields.
        """
        e = cls(1, 2, 3, w=4)
        e2 = pickle.loads(pickle.dumps(e, protocol))

        assert e2.args == (1, 2, 3)
        assert (e2.x, e2.y, e2.z, e2.w) == (1, 2, 3, 4)


@pytest.mark.parametrize(
    "cls",
    DEFAULT_CLASSES
    + FACTORY_CLASSES
    + KW_ONLY_CLASSES
    + MIXED_KW_ONLY_CLASSES
    + [InheritanceLeafError, InheritanceLeafSlotsError],
)
class TestCopy(object):
    def test_copy(self, cls):
        """
        copy.copy preserves args and all fields.
        """
        e = self._make(cls)
        c = copy.copy(e)

        assert c is not e
        assert c.args == e.args
        for a in attr.fields(cls):
            assert getattr(c, a.name) == getattr(e, a.name)

    def test_deepcopy(self, cls):
        """
        copy.deepcopy preserves args and all fields.
        """
        e = self._make(cls)
        d = copy.deepcopy(e)

        assert d.args == e.args
        for a in attr.fields(cls):
            assert getattr(d, a.name) == getattr(e, a.name)

    @staticmethod
    def _make(cls):
        if cls in KW_ONLY_CLASSES:
            return cls(x=1, y=2)
        if cls in FACTORY_CLASSES:
            return cls(1, [1, 2])
        if cls in (InheritanceLeafError, InheritanceLeafSlotsError):
            return cls(1, 2, 3, w=4)
        return cls(1)


@pytest.mark.parametrize(
    "cls",
    [
        DefaultErrorFrozen,
        DefaultErrorSlotsFrozen,
        FactoryErrorFrozen,
        FactoryErrorSlotsFrozen,
        KwOnlyErrorFrozen,
        KwOnlyErrorSlotsFrozen,
    ],
)
class TestFrozen(object):
    def test_frozen_before_pickle(self, cls):
        """
        Instances are frozen.
        """
        with pytest.raises(FrozenInstanceError):
            self._make(cls).x = 99

    def test_frozen_after_pickle(self, cls):
        """
        Unpickled instances stay frozen.
        """
        e2 = pickle.loads(pickle.dumps(self._make(cls)))

        with pytest.raises(FrozenInstanceError):
            e2.x = 99

    @staticmethod
    def _make(cls):
        if cls in KW_ONLY_CLASSES:
            return cls(x=1, y=2)
        if cls in FACTORY_CLASSES:
            return cls(1, [1])
        return cls(1)


class TestInheritance(object):
    def test_multi_level_inheritance(self):
        """
        Fields from all levels are initialized in order and part of args.
        """
        e = InheritanceLeafError(1, 2, 3)

        assert (e.x, e.y, e.z) == (1, 2, 3)
        assert e.args == (1, 2, 3)
        assert isinstance(e, InheritanceBaseError)

    def test_default_added_in_subclass(self):
        """
        A subclass may introduce new defaults.
        """

        @attr.s(auto_exc=True)
        class SubE(InheritanceBaseError):
            y = attr.ib(default=10)

        assert SubE(1).args == (1, 10)
        assert SubE(1, 7).args == (1, 7)

    def test_plain_exception_base(self):
        """
        Non-attrs exception bases work.
        """

        class Plain(Exception):
            pass

        @attr.s(auto_exc=True)
        class E(Plain):
            x = attr.ib()

        assert isinstance(E(5), Plain)
        assert E(5).args == (5,)


class TestChaining(object):
    def test_explicit_chaining(self):
        """
        Explicit exception chaining works like with regular exceptions.
        """

        def f():
            try:
                raise ValueError("inner")
            except ValueError as cause:
                raise SimpleError(1) from cause

        with pytest.raises(SimpleError) as ei:
            f()

        assert ei.value.__cause__.args == ("inner",)
        assert ei.value.__suppress_context__ is True
        assert ei.value.args == (1,)

    def test_implicit_chaining(self):
        """
        Implicit chaining sets __context__.
        """
        with pytest.raises(SimpleError) as ei:
            try:
                raise ValueError("boom")
            except ValueError:
                raise SimpleError(2)

        assert ei.value.__context__.args == ("boom",)
        assert ei.value.__suppress_context__ is False


class TestValidatorsAndPostInit(object):
    def test_validators_still_run(self):
        """
        Validators run before the exception is fully initialized.
        """

        @attr.s(auto_exc=True)
        class E(Exception):
            x = attr.ib(validator=attr.validators.instance_of(int))

        E(1)
        with pytest.raises(TypeError):
            E("nope")

    def test_post_init_runs(self):
        """
        __attrs_post_init__ runs and args is already set.
        """
        seen = {}

        @attr.s(auto_exc=True)
        class E(Exception):
            x = attr.ib()

            def __attrs_post_init__(self):
                seen["args"] = self.args
                self.extra = self.x + 1

        e = E(10)

        assert seen["args"] == (10,)
        assert e.extra == 11
        assert e.args == (10,)

    @pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
    def test_post_init_extra_pickles(self, protocol):
        """
        Non-field instance attributes (e.g. created in post_init) are
        pickled like with regular exceptions.
        """
        e2 = pickle.loads(pickle.dumps(PostInitError(10), protocol))

        assert e2.extra == 11
        assert e2.args == (10,)
