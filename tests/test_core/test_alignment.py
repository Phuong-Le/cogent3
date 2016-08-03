#!/usr/bin/env python

from cogent3.util.unit_test import TestCase, main
from cogent3.core.sequence import RnaSequence, frac_same, ArraySequence, Sequence
from cogent3.maths.stats.util import Freqs, Numbers
from cogent3.core.moltype import RNA, DNA, PROTEIN, BYTES

from cogent3.core.alignment import SequenceCollection, \
    make_gap_filter, coerce_to_string, \
    seqs_from_array, seqs_from_array_seqs, seqs_from_generic, seqs_from_fasta, \
    seqs_from_dict, seqs_from_aln, seqs_from_kv_pairs, seqs_from_empty, \
    aln_from_array, aln_from_array_seqs, aln_from_collection,\
    aln_from_generic, aln_from_fasta, aln_from_array_aln, aln_from_empty, \
    ArrayAlignment, Alignment, DataError

from cogent3.core.moltype import AB, DNA
from cogent3.parse.fasta import MinimalFastaParser
from numpy import array, arange, transpose
from tempfile import mktemp
from os import remove
import re

__author__ = "Rob Knight"
__copyright__ = "Copyright 2007-2016, The Cogent Project"
__credits__ = ["Jeremy Widmann", "Catherine Lozuopone", "Gavin Huttley",
               "Rob Knight", "Daniel McDonald", "Jan Kosinski"]
__license__ = "GPL"
__version__ = "3.0a1"
__maintainer__ = "Rob Knight"
__email__ = "rob@spot.colorado.edu"
__status__ = "Production"


class alignment_tests(TestCase):
    """Tests of top-level functions."""

    def test_seqs_from_array(self):
        """seqs_from_array should return chars, and successive indices."""
        a = array([[0, 1, 2], [2, 1, 0]])  # three 2-char seqs
        obs_a, obs_labels = seqs_from_array(a)
        # note transposition
        self.assertEqual(obs_a, [array([0, 2]), array([1, 1]), array([2, 0])])
        self.assertEqual(obs_labels, None)

    def test_seqs_from_array_seqs(self):
        """seqs_from_array_seqs should return model seqs + names."""
        s1 = ArraySequence('ABC', name='a')
        s2 = ArraySequence('DEF', name='b')
        obs_a, obs_labels = seqs_from_array_seqs([s1, s2])
        self.assertEqual(obs_a, [s1, s2])  # seq -> numbers
        self.assertEqual(obs_labels, ['a', 'b'])

    def test_seqs_from_generic(self):
        """seqs_from_generic should initialize seqs from list of lists, etc."""
        s1 = 'ABC'
        s2 = 'DEF'
        obs_a, obs_labels = seqs_from_generic([s1, s2])
        self.assertEqual(obs_a, ['ABC', 'DEF'])
        self.assertEqual(obs_labels, [None, None])

    def test_seqs_from_fasta(self):
        """seqs_from_fasta should initialize seqs from fasta-format string"""
        s = '>aa\nAB\nC\n>bb\nDE\nF\n'
        obs_a, obs_labels = seqs_from_fasta(s)
        self.assertEqual(obs_a, ['ABC', 'DEF'])
        self.assertEqual(obs_labels, ['aa', 'bb'])

    def test_seqs_from_aln(self):
        """seqs_from_aln should initialize from existing alignment"""
        c = SequenceCollection(['abc', 'def'])
        obs_a, obs_labels = seqs_from_aln(c)
        self.assertEqual(obs_a, ['abc', 'def'])
        self.assertEqual(obs_labels, ['seq_0', 'seq_1'])

    def test_seqs_from_kv_pairs(self):
        """seqs_from_kv_pairs should initialize from key-value pairs"""
        c = [['a', 'abc'], ['b', 'def']]
        obs_a, obs_labels = seqs_from_kv_pairs(c)
        self.assertEqual(obs_a, ['abc', 'def'])
        self.assertEqual(obs_labels, ['a', 'b'])

    def test_seqs_from_empty(self):
        """seqs_from_empty should always raise ValueError"""
        self.assertRaises(ValueError, seqs_from_empty, 'xyz')

    def test_aln_from_array(self):
        """aln_from_array should return same array, and successive indices."""
        a = array([[0, 1, 2], [3, 4, 5]])  # three 2-char seqs
        obs_a, obs_labels = aln_from_array(a)
        self.assertEqual(obs_a, transpose(a))
        self.assertEqual(obs_labels, None)

    def test_aln_from_array_seqs(self):
        """aln_from_array_seqs should initialize aln from sequence objects."""
        s1 = ArraySequence('ACC', name='a', alphabet=RNA.alphabet)
        s2 = ArraySequence('GGU', name='b', alphabet=RNA.alphabet)
        obs_a, obs_labels = aln_from_array_seqs([s1, s2],
                                                alphabet=BYTES.alphabet)
        self.assertEqual(obs_a, array([[2, 1, 1], [3, 3, 0]], 'b'))
        # seq -> numbers
        self.assertEqual(obs_labels, ['a', 'b'])

    def test_aln_from_generic(self):
        """aln_from_generic should initialize aln from list of lists, etc."""
        s1 = 'AAA'
        s2 = 'GGG'
        obs_a, obs_labels = aln_from_generic([s1, s2], 'b',
                                             alphabet=RNA.alphabet)  # specify array type
        self.assertEqual(obs_a, array(
            [[2, 2, 2], [3, 3, 3]], 'b'))  # str -> chars
        self.assertEqual(obs_labels, [None, None])

    def test_aln_from_fasta(self):
        """aln_from_fasta should initialize aln from fasta-format string"""
        s = '>aa\nAB\nC\n>bb\nDE\nF\n'
        obs_a, obs_labels = aln_from_fasta(s.splitlines())
        self.assertEqual(obs_a, array(
            ['ABC', 'DEF'], 'c').view('B'))  # seq -> numbers
        self.assertEqual(obs_labels, ['aa', 'bb'])

    def test_aln_from_array_aln(self):
        """aln_from_array_aln should initialize from existing alignment"""
        a = ArrayAlignment(array([[0, 1, 2], [3, 4, 5]]),
                           conversion_f=aln_from_array)
        obs_a, obs_labels = aln_from_array_aln(a)
        self.assertEqual(obs_a, a.seq_data)
        self.assertEqual(obs_labels, a.names)

    def test_aln_from_collection(self):
        """aln_from_collection should initialize from existing alignment"""
        a = SequenceCollection(['AAA', 'GGG'])
        obs_a, obs_labels = aln_from_collection(a, alphabet=RNA.alphabet)
        self.assertEqual(a.to_fasta(), '>seq_0\nAAA\n>seq_1\nGGG')
        self.assertEqual(obs_a, array([[2, 2, 2], [3, 3, 3]]))

    def test_aln_from_empty(self):
        """aln_from_empty should always raise ValueError"""
        self.assertRaises(ValueError, aln_from_empty, 'xyz')


class SequenceCollectionBaseTests(object):
    """base class for testing the SequenceCollection object.

    Unlike Alignments, SequenceCollections can have sequences that are not equal
    length. This module contains all the code that _doesn't_ depend on being
    able to look at "ragged" SequenceCollections. It is intended that all
    classes that inherit from SequenceCollection should have test classes that
    inherit from this class, but that the SequenceCollection tests themselves
    will additionally contain code to deal with SequenceCollections of unequal
    length.

    set self.Class in subclasses to generate the rught constructor.
    """
    Class = SequenceCollection

    def setUp(self):
        """Define some standard SequenceCollection objects."""
        if type(self.Class) == ArrayAlignment:
            pass

        self.one_seq = self.Class({'a': 'AAAAA'})
        self.ragged_padded = self.Class({'a': 'AAAAAA', 'b': 'AAA---',
                                         'c': 'AAAA--'})
        self.identical = self.Class({'a': 'AAAA', 'b': 'AAAA'})
        self.gaps = self.Class({'a': 'AAAAAAA', 'b': 'A--A-AA',
                                'c': 'AA-----'})
        self.gaps_rna = self.Class({'a': RnaSequence('AAAAAAA'),
                                    'b': RnaSequence('A--A-AA'),
                                    'c': RnaSequence('AA-----')})
        self.unordered = self.Class({'a': 'AAAAA', 'b': 'BBBBB'})
        self.ordered1 = self.Class({'a': 'AAAAA', 'b': 'BBBBB'},
                                   names=['a', 'b'])
        self.ordered2 = self.Class({'a': 'AAAAA', 'b': 'BBBBB'},
                                   names=['b', 'a'])
        self.mixed = self.Class({'a': 'ABCDE', 'b': 'LMNOP'})
        self.end_gaps = self.Class({'a': '--A-BC-', 'b': '-CB-A--',
                                    'c': '--D-EF-'}, names=['a', 'b', 'c'])
        self.many = self.Class({
            'a': RnaSequence('UCAGUCAGUU'),
            'b': RnaSequence('UCCGUCAAUU'),
            'c': RnaSequence('ACCAUCAGUC'),
            'd': RnaSequence('UCAAUCGGUU'),
            'e': RnaSequence('UUGGUUGGGU'),
            'f': RnaSequence('CCGGGCGGCC'),
            'g': RnaSequence('UCAACCGGAA'),
        })
        # Additional SequenceCollections for tests added 6/4/04 by Jeremy
        # Widmann
        self.sequences = self.Class(
            list(map(RnaSequence, ['UCAG', 'UCAG', 'UCAG'])))
        # Additional SequenceCollection for tests added 1/30/06 by Cathy
        # Lozupone
        self.omitSeqsTemplate_aln = self.Class({
            's1': RnaSequence('UC-----CU---C'),
            's2': RnaSequence('UC------U---C'),
            's3': RnaSequence('UUCCUUCUU-UUC'),
            's4': RnaSequence('UU-UUUU-UUUUC'),
            's5': RnaSequence('-------------')
        })

        self.a = ArrayAlignment(['AAA', 'AAA'])
        self.b = Alignment(['AAA', 'AAA'])
        self.c = SequenceCollection(['AAA', 'AAA'])

    def test_guess_input_type(self):
        """SequenceCollection  _guess_input_type should figure out data type correctly"""
        git = self.a._guess_input_type
        self.assertEqual(git(self.a), 'array_aln')
        self.assertEqual(git(self.b), 'aln')
        self.assertEqual(git(self.c), 'collection')
        self.assertEqual(git('>ab\nabc'), 'fasta')
        self.assertEqual(git(['>ab', 'abc']), 'fasta')
        self.assertEqual(git(['abc', 'def']), 'generic')
        # precedence over generic
        self.assertEqual(git([[1, 2], [4, 5]]), 'kv_pairs')
        self.assertEqual(git([[1, 2, 3], [4, 5, 6]]), 'generic')
        self.assertEqual(git([ArraySequence('abc')]), 'array_seqs')
        self.assertEqual(git(array([[1, 2, 3], [4, 5, 6]])), 'array')
        self.assertEqual(git({'a': 'aca'}), 'dict')
        self.assertEqual(git([]), 'empty')

    def test_init_aln(self):
        """ SequenceCollection should init from existing alignments"""
        exp = self.Class(['AAA', 'AAA'])
        x = self.Class(self.a)
        y = self.Class(self.b)
        z = self.Class(self.c)
        self.assertEqual(x, exp)
        self.assertEqual(z, exp)
        self.assertEqual(y, exp)
    test_init_aln.__doc__ = Class.__name__ + test_init_aln.__doc__

    def test_init_dict(self):
        """SequenceCollection init from dict should work as expected"""
        d = {'a': 'AAAAA', 'b': 'BBBBB'}
        a = self.Class(d, names=['a', 'b'])
        self.assertEqual(a, d)
        self.assertEqual(list(a.named_seqs.items()), list(d.items()))

    def test_init_name_mapped(self):
        """SequenceCollection init should allow name mapping function"""
        d = {'a': 'AAAAA', 'b': 'BBBBB'}
        f = lambda x: x.upper()
        a = self.Class(d, label_to_name=f)
        self.assertNotEqual(a, d)
        self.assertNotEqual(sorted(a.named_seqs.items()), sorted(d.items()))
        d_upper = {'A': 'AAAAA', 'B': 'BBBBB'}
        self.assertEqual(a, d_upper)
        self.assertEqual(sorted(a.named_seqs.items()), sorted(d_upper.items()))

    def test_init_seq(self):
        """SequenceCollection init from list of sequences should use indices as keys"""
        seqs = ['AAAAA', 'BBBBB', 'CCCCC']
        a = self.Class(seqs)
        self.assertEqual(len(a.named_seqs), 3)
        self.assertEqual(a.named_seqs['seq_0'], 'AAAAA')
        self.assertEqual(a.named_seqs['seq_1'], 'BBBBB')
        self.assertEqual(a.named_seqs['seq_2'], 'CCCCC')
        self.assertEqual(a.names, ['seq_0', 'seq_1', 'seq_2'])
        self.assertEqual(list(a.seqs), ['AAAAA', 'BBBBB', 'CCCCC'])

    def test_init_annotated_seq(self):
        """SequenceCollection init from seqs w/ info should preserve data"""
        a = Sequence('AAA', name='a', info={'x': 3})
        b = Sequence('CCC', name='b', info={'x': 4})
        c = Sequence('GGG', name='c', info={'x': 5})
        seqs = [c, b, a]
        a = self.Class(seqs)
        self.assertEqual(list(a.names), ['c', 'b', 'a'])
        self.assertEqual(list(map(str, a.seqs)), ['GGG', 'CCC', 'AAA'])
        if self.Class is not ArrayAlignment:
            # ArrayAlignment is allowed to strip info objects
            self.assertEqual([i.info.x for i in a.seqs], [5, 4, 3])
        # check it still works if constructed from same class
        b = self.Class(a)
        self.assertEqual(list(b.names), ['c', 'b', 'a'])
        self.assertEqual(list(map(str, b.seqs)), ['GGG', 'CCC', 'AAA'])
        if self.Class is not ArrayAlignment:
            # ArrayAlignment is allowed to strip Info objects
            self.assertEqual([i.info.x for i in b.seqs], [5, 4, 3])

    def test_init_pairs(self):
        """SequenceCollection init from list of (key,val) pairs should work correctly"""
        seqs = [['x', 'XXX'], ['b', 'BBB'], ['c', 'CCC']]
        a = self.Class(seqs)
        self.assertEqual(len(a.named_seqs), 3)
        self.assertEqual(a.named_seqs['x'], 'XXX')
        self.assertEqual(a.named_seqs['b'], 'BBB')
        self.assertEqual(a.named_seqs['c'], 'CCC')
        self.assertEqual(a.names, ['x', 'b', 'c'])
        self.assertEqual(list(a.seqs), ['XXX', 'BBB', 'CCC'])

    def test_init_duplicate_keys(self):
        """SequenceCollection init from (key, val) pairs should fail on dup. keys"""
        seqs = [['x', 'XXX'], ['b', 'BBB'], [
            'x', 'CCC'], ['d', 'DDD'], ['a', 'AAA']]
        self.assertRaises(ValueError, self.Class, seqs)
        aln = self.Class(seqs, remove_duplicate_names=True)
        self.assertEqual(str(self.Class(seqs, remove_duplicate_names=True)),
                         '>x\nXXX\n>b\nBBB\n>d\nDDD\n>a\nAAA\n')

    def test_init_ordered(self):
        """SequenceCollection should iterate over seqs correctly even if ordered"""
        first = self.ordered1
        sec = self.ordered2
        un = self.unordered

        self.assertEqual(first.names, ['a', 'b'])
        self.assertEqual(sec.names, ['b', 'a'])
        self.assertEqual(set(un.names), set(un.named_seqs.keys()))

        first_list = list(first.seqs)
        sec_list = list(sec.seqs)
        un_list = list(un.seqs)

        self.assertEqual(first_list, ['AAAAA', 'BBBBB'])
        self.assertEqual(sec_list, ['BBBBB', 'AAAAA'])

        # check that the unordered seq matches one of the lists
        self.assertTrue((un_list == first_list) or (un_list == sec_list))
        self.assertNotEqual(first_list, sec_list)

    def test_init_ambig(self):
        """SequenceCollection should tolerate ambiguous chars"""
        aln = self.Class(['AAA', 'CCC'], moltype=DNA)
        aln = self.Class(['ANS', 'CWC'], moltype=DNA)
        aln = self.Class(['A-A', 'CC-'], moltype=DNA)
        aln = self.Class(['A?A', 'CC-'], moltype=DNA)

    def test_aln_from_fasta_parser(self):
        """aln_from_fasta_parser should init from iterator"""
        s = '>aa\nAC\n>bb\nAA\n>c\nGG\n'.splitlines()
        p = MinimalFastaParser(s)
        aln = self.Class(p, moltype=DNA)
        self.assertEqual(aln.named_seqs['aa'], 'AC')
        self.assertEqual(aln.to_fasta(), '>aa\nAC\n>bb\nAA\n>c\nGG')
        s2_ORIG = '>x\nCA\n>b\nAA\n>>xx\nGG'
        s2 = '>aa\nAC\n>bb\nAA\n>c\nGG\n'
        d = ArrayAlignment(MinimalFastaParser(s2.splitlines()))
        da = d.to_fasta()
        self.assertEqual(d.to_fasta(), aln.to_fasta())

    def test_aln_from_fasta(self):
        """SequenceCollection should init from fasta-format string"""
        s = '>aa\nAC\n>bb\nAA\n>c\nGG\n'
        aln = self.Class(s)
        self.assertEqual(aln.to_fasta(), s.strip())

    def test_seq_len_get(self):
        """SequenceCollection seq_len should return length of longest seq"""
        self.assertEqual(self.one_seq.seq_len, 5)
        self.assertEqual(self.identical.seq_len, 4)
        self.assertEqual(self.gaps.seq_len, 7)

    def test_Seqs(self):
        """SequenceCollection seqs property should return seqs in correct order."""
        first = self.ordered1
        sec = self.ordered2
        un = self.unordered

        first_list = list(first.seqs)
        sec_list = list(sec.seqs)
        un_list = list(un.seqs)

        self.assertEqual(first_list, ['AAAAA', 'BBBBB'])
        self.assertEqual(sec_list, ['BBBBB', 'AAAAA'])

        # check that the unordered seq matches one of the lists
        self.assertTrue((un_list == first_list) or (un_list == sec_list))
        self.assertNotEqual(first_list, sec_list)

    def test_iter_seqs(self):
        """SequenceCollection iter_seqs() method should support reordering of seqs"""
        self.ragged_padded = self.Class(self.ragged_padded.named_seqs,
                                        names=['a', 'b', 'c'])
        seqs = list(self.ragged_padded.iter_seqs())
        self.assertEqual(seqs, ['AAAAAA', 'AAA---', 'AAAA--'])
        seqs = list(self.ragged_padded.iter_seqs(seq_order=['b', 'a', 'a']))
        self.assertEqual(seqs, ['AAA---', 'AAAAAA', 'AAAAAA'])
        self.assertSameObj(seqs[1], seqs[2])
        self.assertSameObj(seqs[0], self.ragged_padded.named_seqs['b'])

    def test_Items(self):
        """SequenceCollection iter_selected should iterate over items in specified order."""
        # should work if one row
        self.assertEqual(list(self.one_seq.iter_selected()), ['A'] * 5)
        # should take order into account
        self.assertEqual(list(self.ordered1.iter_selected()), ['A'] * 5 + ['B'] * 5)
        self.assertEqual(list(self.ordered2.iter_selected()), ['B'] * 5 + ['A'] * 5)

    def test_iter_selected(self):
        """SequenceCollection iter_selected() should iterate over items in correct order"""
        # should work if one row
        self.assertEqual(list(self.one_seq.iter_selected()), ['A'] * 5)
        # should take order into account
        self.assertEqual(list(self.ordered1.iter_selected()),
                         ['A'] * 5 + ['B'] * 5)
        self.assertEqual(list(self.ordered2.iter_selected()),
                         ['B'] * 5 + ['A'] * 5)
        # should allow row and/or col specification
        r = self.ragged_padded
        self.assertEqual(list(r.iter_selected(seq_order=['c', 'b'],
                                          pos_order=[5, 1, 3])), list('-AA-A-'))
        # should not interfere with superclass iteritems()
        i = list(r.named_seqs.items())
        i.sort()
        self.assertEqual(
            i, [('a', 'AAAAAA'), ('b', 'AAA---'), ('c', 'AAAA--')])

    def test_take_seqs(self):
        """SequenceCollection take_seqs should return new SequenceCollection with selected seqs."""
        a = self.ragged_padded.take_seqs('bc')
        self.assertTrue(isinstance(a, SequenceCollection))
        self.assertEqual(a, {'b': 'AAA---', 'c': 'AAAA--'})
        # should be able to negate
        a = self.ragged_padded.take_seqs('bc', negate=True)
        self.assertEqual(a, {'a': 'AAAAAA'})

    def test_take_seqs_moltype(self):
        """take_seqs should preserve the MolType"""
        orig = self.Class(
            data={'a': 'CCCCCC', 'b': 'AAA---', 'c': 'AAAA--'}, moltype=DNA)
        subset = orig.take_seqs('ab')
        self.assertEqual(set(subset.moltype), set(orig.moltype))

    def test_get_seq_indices(self):
        """SequenceCollection get_seq_indices should return names of seqs where f(row) is True"""
        srp = self.ragged_padded
        is_long = lambda x: len(x) > 10
        is_med = lambda x: len(str(x).replace('-', '')) > 3  # strips gaps
        is_any = lambda x: len(x) > 0
        self.assertEqual(srp.get_seq_indices(is_long), [])
        srp.names = 'cba'
        self.assertEqual(srp.get_seq_indices(is_med), ['c', 'a'])
        srp.names = 'bac'
        self.assertEqual(srp.get_seq_indices(is_med), ['a', 'c'])
        self.assertEqual(srp.get_seq_indices(is_any), ['b', 'a', 'c'])
        # should be able to negate
        self.assertEqual(srp.get_seq_indices(is_med, negate=True), ['b'])
        self.assertEqual(srp.get_seq_indices(is_any, negate=True), [])

    def test_take_seqs_if(self):
        """SequenceCollection take_seqs_if should return seqs where f(row) is True"""
        is_long = lambda x: len(x) > 10
        is_med = lambda x: len(str(x).replace('-', '')) > 3
        is_any = lambda x: len(x) > 0
        srp = self.ragged_padded
        self.assertEqual(srp.take_seqs_if(is_long), {})
        srp.names = 'cba'
        self.assertEqual(srp.take_seqs_if(is_med),
                         {'c': 'AAAA--', 'a': 'AAAAAA'})
        srp.names = list(srp.named_seqs.keys())
        self.assertEqual(srp.take_seqs_if(is_med),
                         {'c': 'AAAA--', 'a': 'AAAAAA'})
        self.assertEqual(srp.take_seqs_if(is_any), srp)
        self.assertTrue(isinstance(srp.take_seqs_if(is_med), SequenceCollection))
        # should be able to negate
        self.assertEqual(srp.take_seqs_if(is_med, negate=True),
                         {'b': 'AAA---'})

    def test_get_items(self):
        """SequenceCollection get_items should return list of items from k,v pairs"""
        self.assertEqual(self.mixed.get_items([('a', 3), ('b', 4), ('a', 0)]),
                         ['D', 'P', 'A'])
        self.assertRaises(KeyError, self.mixed.get_items, [('x', 'y')])
        self.assertRaises(IndexError, self.mixed.get_items, [('a', 1000)])
        # should be able to negate -- note that results will have seqs in
        # arbitrary order
        self.assertEqualItems(self.mixed.get_items([('a', 3), ('b', 4), ('a', 0)],
                                                  negate=True), ['B', 'C', 'E', 'L', 'M', 'N', 'O'])

    def test_item_indices_if(self):
        """SequenceCollection item_indices_if should return coordinates of matching items"""
        is_vowel = lambda x: x in 'AEIOU'
        # reverse name order to test that it's not alphabetical
        self.mixed = self.Class(self.mixed.named_seqs, names=['b', 'a'])
        self.assertEqual(self.mixed.item_indices_if(is_vowel),
                         [('b', 3), ('a', 0), ('a', 4)])
        is_lower = lambda x: x.islower()
        self.assertEqual(self.ragged_padded.item_indices_if(is_lower), [])
        # should be able to negate
        self.assertEqualItems(self.mixed.item_indices_if(is_vowel, negate=True),
                              [('a', 1), ('a', 2), ('a', 3), ('b', 0), ('b', 1), ('b', 2), ('b', 4)])

    def test_items_if(self):
        """SequenceCollection items_if should return matching items"""
        is_vowel = lambda x: x in 'AEIOU'
        # reverse name order to test that it's not alphabetical
        self.mixed = self.Class(self.mixed.named_seqs, names=['b', 'a'])
        self.assertEqual(self.mixed.items_if(is_vowel), ['O', 'A', 'E'])
        self.assertEqual(self.one_seq.items_if(is_vowel), list('AAAAA'))
        # should be able to negate
        self.assertEqualItems(self.mixed.items_if(is_vowel, negate=True),
                              list('BCDLMNP'))

    def test_get_similar(self):
        """SequenceCollection get_similar should get all sequences close to target seq"""
        aln = self.many
        x = RnaSequence('GGGGGGGGGG')
        y = RnaSequence('----------')
        # test min and max similarity ranges
        result = aln.get_similar(aln.named_seqs['a'], min_similarity=0.4,
                                max_similarity=0.7)
        for seq in 'cefg':
            self.assertContains(result.named_seqs, seq)
            self.assertEqual(result.named_seqs[seq], aln.named_seqs[seq])
        self.assertEqual(len(result.named_seqs), 4)

        result = aln.get_similar(aln.named_seqs['a'], min_similarity=0.95,
                                max_similarity=1)
        for seq in 'a':
            self.assertContains(result.named_seqs, seq)
            self.assertEqual(result.named_seqs[seq], aln.named_seqs[seq])
        self.assertEqual(len(result.named_seqs), 1)

        result = aln.get_similar(aln.named_seqs['a'], min_similarity=0.75,
                                max_similarity=0.85)
        for seq in 'bd':
            self.assertContains(result.named_seqs, seq)
            self.assertEqual(result.named_seqs[seq], aln.named_seqs[seq])
        self.assertEqual(len(result.named_seqs), 2)

        result = aln.get_similar(aln.named_seqs['a'], min_similarity=0,
                                max_similarity=0.2)
        self.assertEqual(result, {})

        # test some sequence transformations
        transform = lambda s: s[1:4]
        result = aln.get_similar(aln.named_seqs['a'], min_similarity=0.5,
                                transform=transform)
        for seq in 'abdfg':
            self.assertContains(result.named_seqs, seq)
            self.assertEqual(result.named_seqs[seq], aln.named_seqs[seq])
        self.assertEqual(len(result.named_seqs), 5)

        transform = lambda s: s[-3:]
        result = aln.get_similar(aln.named_seqs['a'], min_similarity=0.5,
                                transform=transform)
        for seq in 'abcde':
            self.assertContains(result.named_seqs, seq)
            self.assertEqual(result.named_seqs[seq], aln.named_seqs[seq])
        self.assertEqual(len(result.named_seqs), 5)

        # test a different distance metric
        metric = lambda x, y: str(x).count('G') + str(y).count('G')
        result = aln.get_similar(aln.named_seqs['a'], min_similarity=5,
                                max_similarity=10, metric=metric)
        for seq in 'ef':
            self.assertContains(result.named_seqs, seq)
            self.assertEqual(result.named_seqs[seq], aln.named_seqs[seq])
        self.assertEqual(len(result.named_seqs), 2)

        # test the combination of a transform and a distance metric
        aln = self.Class(dict(enumerate(map(RnaSequence,
                                            ['GA-GU', 'A-GAC', 'GG-GG']))), moltype=RNA)
        transform = lambda s: RnaSequence(str(s).replace('G', 'A'
                                                         ).replace('U', 'C'))
        metric = RnaSequence.frac_same_non_gaps
        null_transform = lambda s: RnaSequence(str(s))
        # first, do it without the transformation
        try:
            result = aln.get_similar(aln.named_seqs[0], min_similarity=0.5,
                                    metric=metric)
        except TypeError:  # need to coerce to RNA seq w/ null_transform
            result = aln.get_similar(aln.named_seqs[0], min_similarity=0.5,
                                    metric=metric, transform=null_transform)
        for seq in [0, 2]:
            self.assertContains(result.named_seqs, seq)
            self.assertEqual(result.named_seqs[seq], aln.named_seqs[seq])
        self.assertEqual(len(result.named_seqs), 2)
        # repeat with higher similarity
        try:
            result = aln.get_similar(aln.named_seqs[0], min_similarity=0.8,
                                    metric=metric)
        except TypeError:  # need to coerce to RNA
            result = aln.get_similar(aln.named_seqs[0], min_similarity=0.8,
                                    metric=metric, transform=null_transform)
        for seq in [0]:
            self.assertContains(result.named_seqs, seq)
            self.assertEqual(result.named_seqs[seq], aln.named_seqs[seq])
        self.assertEqual(len(result.named_seqs), 1)
        # then, verify that the transform changes the results
        result = aln.get_similar(aln.named_seqs[0], min_similarity=0.5,
                                metric=metric, transform=transform)
        for seq in [0, 1, 2]:
            self.assertContains(result.named_seqs, seq)
            self.assertEqual(result.named_seqs[seq], aln.named_seqs[seq])
        self.assertEqual(len(result.named_seqs), 3)

        result = aln.get_similar(aln.named_seqs[0], min_similarity=0.8,
                                metric=metric, transform=transform)
        for seq in [0, 1]:
            self.assertContains(result.named_seqs, seq)
            self.assertEqual(result.named_seqs[seq], aln.named_seqs[seq])
        self.assertEqual(len(result.named_seqs), 2)

    def test_distance_matrix(self):
        """SequenceCollection distance_matrix should produce correct scores"""
        self.assertEqual(self.one_seq.distance_matrix(
            frac_same), {'a': {'a': 1}})
        self.assertEqual(self.gaps.distance_matrix(frac_same),
                         {'a': {'a': 7 / 7.0, 'b': 4 / 7.0, 'c': 2 / 7.0},
                             'b': {'a': 4 / 7.0, 'b': 7 / 7.0, 'c': 3 / 7.0},
                             'c': {'a': 2 / 7.0, 'b': 3 / 7.0, 'c': 7 / 7.0},
            })

    def test_is_ragged(self):
        """SequenceCollection is_ragged should return true if ragged alignment"""
        assert(not self.identical.is_ragged())
        assert(not self.gaps.is_ragged())

    def test_to_phylip(self):
        """SequenceCollection should return PHYLIP string format correctly"""
        align_norm = self.Class(['ACDEFGHIKLMNPQRSTUVWY-',
                                  'ACDEFGHIKLMNPQRSUUVWF-',
                                  'ACDEFGHIKLMNPERSKUVWC-',
                                  'ACNEFGHIKLMNPQRS-UVWP-',
                                  ])

        phylip_str, id_map = align_norm.to_phylip()

        self.assertEqual(
            phylip_str, """4 22\nseq0000001 ACDEFGHIKLMNPQRSTUVWY-\nseq0000002 ACDEFGHIKLMNPQRSUUVWF-\nseq0000003 ACDEFGHIKLMNPERSKUVWC-\nseq0000004 ACNEFGHIKLMNPQRS-UVWP-""")
        self.assertEqual(id_map, {'seq0000004': 'seq_3', 'seq0000001': 'seq_0',
                                  'seq0000003': 'seq_2', 'seq0000002': 'seq_1'})

    def test_to_fasta(self):
        """SequenceCollection should return correct FASTA string"""
        aln = self.Class(['AAA', 'CCC'])
        self.assertEqual(aln.to_fasta(), '>seq_0\nAAA\n>seq_1\nCCC')

        # NOTE THE FOLLOWING SURPRISING BEHAVIOR BECAUSE OF THE TWO-ITEM
        # SEQUENCE RULE:
        aln = self.Class(['AA', 'CC'])
        self.assertEqual(aln.to_fasta(), '>A\nA\n>C\nC')

    def test_to_nexus(self):
        """SequenceCollection should return correct Nexus string format"""
        align_norm = self.Class(['ACDEFGHIKLMNPQRSTUVWY-',
                                  'ACDEFGHIKLMNPQRSUUVWF-',
                                  'ACDEFGHIKLMNPERSKUVWC-',
                                  'ACNEFGHIKLMNPQRS-UVWP-'])
        expect = '#NEXUS\n\nbegin data;\n'\
            '    dimensions ntax=4 nchar=22;\n'\
            '    format datatype=protein interleave=yes missing=? gap=-;\n'\
            '    matrix\n'\
            '    seq_0    ACDEFGHIKLMNPQRSTUVWY-\n'\
            '    seq_1    ACDEFGHIKLMNPQRSUUVWF-\n'\
            '    seq_2    ACDEFGHIKLMNPERSKUVWC-\n'\
            '    seq_3    ACNEFGHIKLMNPQRS-UVWP-\n\n    ;\nend;'
        got = align_norm.to_nexus('protein')
        self.assertEqual(got, expect)

    def test_get_int_map(self):
        """SequenceCollection.get_int_map should return correct mapping."""
        aln = self.Class({'seq1': 'ACGU', 'seq2': 'CGUA', 'seq3': 'CCGU'})
        int_keys = {'seq_0': 'seq1', 'seq_1': 'seq2', 'seq_2': 'seq3'}
        int_map = {'seq_0': 'ACGU', 'seq_1': 'CGUA', 'seq_2': 'CCGU'}
        im, ik = aln.get_int_map()
        self.assertEqual(ik, int_keys)
        self.assertEqual(im, int_map)
        # test change prefix from default 'seq_'
        prefix = 'seqn_'
        int_keys = {'seqn_0': 'seq1', 'seqn_1': 'seq2', 'seqn_2': 'seq3'}
        int_map = {'seqn_0': 'ACGU', 'seqn_1': 'CGUA', 'seqn_2': 'CCGU'}
        im, ik = aln.get_int_map(prefix=prefix)
        self.assertEqual(ik, int_keys)
        self.assertEqual(im, int_map)

    def test_num_seqs(self):
        """SequenceCollection.num_seqs should count seqs."""
        aln = self.Class({'seq1': 'ACGU', 'seq2': 'CGUA', 'seq3': 'CCGU'})
        self.assertEqual(aln.num_seqs, 3)

    def test_copy_annotations(self):
        """SequenceCollection copy_annotations should copy from seq objects"""
        aln = self.Class({'seq1': 'ACGU', 'seq2': 'CGUA', 'seq3': 'CCGU'})
        seq_1 = Sequence('ACGU', name='seq1')
        seq_1.add_feature('xyz', 'abc', [(1, 2)])
        seq_5 = Sequence('ACGUAAAAAA', name='seq5')
        seq_5.add_feature('xyzzz', 'abc', [(1, 2)])
        annot = {'seq1': seq_1, 'seq5': seq_5}
        aln.copy_annotations(annot)
        aln_seq_1 = aln.named_seqs['seq1']
        if not hasattr(aln_seq_1, 'annotations'):
            aln_seq_1 = aln_seq_1.data
        aln_seq_2 = aln.named_seqs['seq2']
        if not hasattr(aln_seq_2, 'annotations'):
            aln_seq_2 = aln_seq_2.data
        self.assertEqual(len(aln_seq_1.annotations), 1)
        self.assertEqual(aln_seq_1.annotations[0].name, 'abc')
        self.assertEqual(len(aln_seq_2.annotations), 0)

    def test_annotate_from_gff(self):
        """SequenceCollection.annotate_from_gff should read gff features"""
        aln = self.Class({'seq1': 'ACGU', 'seq2': 'CGUA', 'seq3': 'CCGU'})
        gff = [
            ['seq1', 'prog1', 'snp', '1', '2', '1.0', '+', '1', '"abc"'],
            ['seq5', 'prog2', 'snp', '2', '3', '1.0', '+', '1', '"yyy"'],
        ]
        gff = list(map('\t'.join, gff))
        aln.annotate_from_gff(gff)
        aln_seq_1 = aln.named_seqs['seq1']
        if not hasattr(aln_seq_1, 'annotations'):
            aln_seq_1 = aln_seq_1.data
        aln_seq_2 = aln.named_seqs['seq2']
        if not hasattr(aln_seq_2, 'annotations'):
            aln_seq_2 = aln_seq_2.data
        self.assertEqual(len(aln_seq_1.annotations), 1)
        self.assertEqual(aln_seq_1.annotations[0].name, 'abc')
        self.assertEqual(len(aln_seq_2.annotations), 0)

    def test_get_gapped_seq(self):
        """SequenceCollection.get_gapped_seq should return seq, with gaps"""
        aln = self.Class({'seq1': '--TTT?', 'seq2': 'GATC??'})
        self.assertEqual(str(aln.get_gapped_seq('seq1')), '--TTT?')

    def test_add(self):
        """__add__ should concatenate sequence data, by name"""
        align1 = self.Class({'a': 'AAAA', 'b': 'TTTT', 'c': 'CCCC'})
        align2 = self.Class({'a': 'GGGG', 'b': '----', 'c': 'NNNN'})
        align = align1 + align2
        concatdict = align.todict()
        self.assertEqual(
            concatdict, {'a': 'AAAAGGGG', 'b': 'TTTT----', 'c': 'CCCCNNNN'})

    def test_add_seqs(self):
        """add_seqs should return an alignment with the new sequences appended or inserted"""
        data = [('name1', 'AAA'), ('name2', 'AAA'),
                 ('name3', 'AAA'), ('name4', 'AAA')]
        data1 = [('name1', 'AAA'), ('name2', 'AAA')]
        data2 = [('name3', 'AAA'), ('name4', 'AAA')]
        data3 = [('name5', 'BBB'), ('name6', 'CCC')]
        aln = self.Class(data)
        aln3 = self.Class(data3)

        out_aln = aln.add_seqs(aln3)
        # test append at the end
        self.assertEqual(str(out_aln), str(self.Class(data + data3)))

        out_aln = aln.add_seqs(aln3, before_name='name3')
        self.assertEqual(str(out_aln), str(self.Class(
            data1 + data3 + data2)))  # test insert before

        out_aln = aln.add_seqs(aln3, after_name='name2')
        self.assertEqual(str(out_aln), str(self.Class(
            data1 + data3 + data2)))  # test insert after

        out_aln = aln.add_seqs(aln3, before_name='name1')
        # test if insert before first seq works
        self.assertEqual(str(out_aln), str(self.Class(data3 + data)))

        out_aln = aln.add_seqs(aln3, after_name='name4')
        # test if insert after last seq works
        self.assertEqual(str(out_aln), str(self.Class(data + data3)))

        self.assertRaises(ValueError, aln.add_seqs, aln3,
                          before_name='name5')  # wrong after/before name
        self.assertRaises(ValueError, aln.add_seqs, aln3,
                          after_name='name5')  # wrong after/before name

        if isinstance(aln, Alignment) or isinstance(aln, ArrayAlignment):
            self.assertRaises((DataError, ValueError),
                              aln.add_seqs, aln3 + aln3)
        else:
            exp = set([seq for name, seq in data])
            exp.update([seq + seq for name, seq in data3])
            got = set()
            for seq in aln.add_seqs(aln3 + aln3).seqs:
                got.update([str(seq).strip()])
            self.assertEqual(got, exp)

    def test_write(self):
        """SequenceCollection.write should write in correct format"""
        aln = self.Class([('a', 'AAAA'), ('b', 'TTTT'), ('c', 'CCCC')])
        fn = mktemp(suffix='.fasta')
        aln.write(fn)
        with open(fn, newline=None) as infile:
            result = infile.read()
        self.assertEqual(result, '>a\nAAAA\n>b\nTTTT\n>c\nCCCC\n')
        remove(fn)

    def test_len(self):
        """len(SequenceCollection) returns length of longest sequence"""
        aln = self.Class([('a', 'AAAA'), ('b', 'TTTT'), ('c', 'CCCC')])
        self.assertEqual(len(aln), 4)

    def test_get_translation(self):
        """SequenceCollection.get_translation translates each seq"""
        for seqs in [
                {'seq1': 'GATTTT', 'seq2': 'GATC??'},
                {'seq1': 'GAT---', 'seq2': '?GATCT'}]:
            alignment = self.Class(data=seqs, moltype=DNA)
            self.assertEqual(len(alignment.get_translation()), 2)
            # check for a failure when no moltype specified
            alignment = self.Class(data=seqs)
            try:
                peps = alignment.get_translation()
            except AttributeError:
                pass

    def test_get_seq(self):
        """SequenceCollection.get_seq should return specified seq"""
        aln = self.Class({'seq1': 'GATTTT', 'seq2': 'GATC??'})
        self.assertEqual(aln.get_seq('seq1'), 'GATTTT')
        self.assertRaises(KeyError, aln.get_seq, 'seqx')

    def test_todict(self):
        """SequenceCollection.todict should return dict of strings (not obj)"""
        aln = self.Class({'seq1': 'GATTTT', 'seq2': 'GATC??'})
        self.assertEqual(aln.todict(), {'seq1': 'GATTTT', 'seq2': 'GATC??'})
        for i in list(aln.todict().values()):
            assert isinstance(i, str)

    def test_get_ambiguous_positions(self):
        """SequenceCollection.get_ambiguous_positions should return pos"""
        aln = self.Class({'s1': 'ATGRY?', 's2': 'T-AG??'}, moltype=DNA)
        self.assertEqual(aln.get_ambiguous_positions(),
                         {'s2': {4: '?', 5: '?'}, 's1': {3: 'R', 4: 'Y', 5: '?'}})

    def test_degap(self):
        """SequenceCollection.degap should strip gaps from each seq"""
        aln = self.Class({'s1': 'ATGRY?', 's2': 'T-AG??'}, moltype=DNA)
        self.assertEqual(aln.degap(), {'s1': 'ATGRY', 's2': 'TAG'})

    def test_with_modified_termini(self):
        """SequenceCollection.with_modified_termini should code trailing gaps as ?"""
        aln = self.Class({'s1': 'AATGR--', 's2': '-T-AG?-'}, moltype=DNA)
        self.assertEqual(aln.with_modified_termini(),
                         {'s1': 'AATGR??', 's2': '?T-AG??'})

    def test_make_gap_filter(self):
        """make_gap_filter returns f(seq) -> True if aligned ok w/ query"""
        s1 = RnaSequence('UC-----CU---C')
        s3 = RnaSequence('UUCCUUCUU-UUC')
        s4 = RnaSequence('UU-UUUU-UUUUC')
        # check that the behavior is ok for gap runs
        f1 = make_gap_filter(s1, 0.9, 5)
        f3 = make_gap_filter(s3, 0.9, 5)
        # Should return False since s1 has gap run >= 5 with respect to s3
        self.assertEqual(f3(s1), False)
        # Should return False since s3 has an insertion run >= 5 to s1
        self.assertEqual(f1(s3), False)
        # Should retun True since s4 does not have a long enough gap or ins run
        self.assertEqual(f3(s4), True)
        f3 = make_gap_filter(s3, 0.9, 6)
        self.assertEqual(f3(s1), True)

        # Check that behavior is ok for gap_fractions
        f1 = make_gap_filter(s1, 0.5, 6)
        f3 = make_gap_filter(s3, 0.5, 6)
        # Should return False since 0.53% of positions are diff for gaps
        self.assertEqual(f3(s1), False)
        self.assertEqual(f1(s3), False)
        self.assertEqual(f3(s4), True)

    def test_omit_gap_seqs(self):
        """SequenceCollection omit_gap_seqs should return alignment w/o seqs with gaps"""
        # check default params
        self.assertEqual(self.gaps.omit_gap_seqs(), self.gaps.omit_gap_seqs(0))
        # check for boundary effects
        self.assertEqual(self.gaps.omit_gap_seqs(-1), {})
        self.assertEqual(self.gaps.omit_gap_seqs(0), {'a': 'AAAAAAA'})
        self.assertEqual(self.gaps.omit_gap_seqs(0.1), {'a': 'AAAAAAA'})
        self.assertEqual(self.gaps.omit_gap_seqs(
            3.0 / 7 - 0.01), {'a': 'AAAAAAA'})
        self.assertEqual(self.gaps.omit_gap_seqs(3.0 / 7),
                         {'a': 'AAAAAAA', 'b': 'A--A-AA'})
        self.assertEqual(self.gaps.omit_gap_seqs(3.0 / 7 + 0.01),
                         {'a': 'AAAAAAA', 'b': 'A--A-AA'})
        self.assertEqual(self.gaps.omit_gap_seqs(5.0 / 7 - 0.01),
                         {'a': 'AAAAAAA', 'b': 'A--A-AA'})
        self.assertEqual(self.gaps.omit_gap_seqs(5.0 / 7 + 0.01), self.gaps)
        self.assertEqual(self.gaps.omit_gap_seqs(0.99), self.gaps)
        # check new object creation
        self.assertNotSameObj(self.gaps.omit_gap_seqs(0.99), self.gaps)
        self.assertTrue(isinstance(self.gaps.omit_gap_seqs(3.0 / 7),
                                   SequenceCollection))
        # repeat tests for object that supplies its own gaps
        self.assertEqual(self.gaps_rna.omit_gap_seqs(-1), {})
        self.assertEqual(self.gaps_rna.omit_gap_seqs(0), {'a': 'AAAAAAA'})
        self.assertEqual(self.gaps_rna.omit_gap_seqs(0.1), {'a': 'AAAAAAA'})
        self.assertEqual(self.gaps_rna.omit_gap_seqs(3.0 / 7 - 0.01),
                         {'a': 'AAAAAAA'})
        self.assertEqual(self.gaps_rna.omit_gap_seqs(3.0 / 7),
                         {'a': 'AAAAAAA', 'b': 'A--A-AA'})
        self.assertEqual(self.gaps_rna.omit_gap_seqs(3.0 / 7 + 0.01),
                         {'a': 'AAAAAAA', 'b': 'A--A-AA'})
        self.assertEqual(self.gaps_rna.omit_gap_seqs(5.0 / 7 - 0.01),
                         {'a': 'AAAAAAA', 'b': 'A--A-AA'})
        self.assertEqual(self.gaps_rna.omit_gap_seqs(
            5.0 / 7 + 0.01), self.gaps_rna)
        self.assertEqual(self.gaps_rna.omit_gap_seqs(0.99), self.gaps_rna)
        self.assertNotSameObj(self.gaps_rna.omit_gap_seqs(0.99), self.gaps_rna)
        self.assertTrue(isinstance(self.gaps_rna.omit_gap_seqs(3.0 / 7),
                                   SequenceCollection))

    def test_omit_gap_runs(self):
        """SequenceCollection omit_gap_runs should return alignment w/o runs of gaps"""
        # negative value will still let through ungapped sequences
        self.assertEqual(self.gaps.omit_gap_runs(-5), {'a': 'AAAAAAA'})
        # test edge effects
        self.assertEqual(self.gaps.omit_gap_runs(0), {'a': 'AAAAAAA'})
        self.assertEqual(self.gaps.omit_gap_runs(1), {'a': 'AAAAAAA'})
        self.assertEqual(self.gaps.omit_gap_runs(
            2), {'a': 'AAAAAAA', 'b': 'A--A-AA'})
        self.assertEqual(self.gaps.omit_gap_runs(
            3), {'a': 'AAAAAAA', 'b': 'A--A-AA'})
        self.assertEqual(self.gaps.omit_gap_runs(
            4), {'a': 'AAAAAAA', 'b': 'A--A-AA'})
        self.assertEqual(self.gaps.omit_gap_runs(5), self.gaps)
        self.assertEqual(self.gaps.omit_gap_runs(6), self.gaps)
        self.assertEqual(self.gaps.omit_gap_runs(1000), self.gaps)
        # test new object creation
        self.assertNotSameObj(self.gaps.omit_gap_runs(6), self.gaps)
        self.assertTrue(isinstance(self.gaps.omit_gap_runs(6),
                                   SequenceCollection))

    def test_consistent_gap_degen_handling(self):
        """gap degen character should be treated consistently"""
        # the degen character '?' can be a gap, so when we strip gaps it should
        # be gone too
        raw_seq = "---??-??TC-GGCG-GCA-G-GC-?-C-TAN-GCGC-CCTC-AGGA?-???-??--"
        raw_ungapped = re.sub("[-?]", "", raw_seq)
        raw_no_ambigs = re.sub("[N?]+", "", raw_seq)
        dna = DNA.make_seq(raw_seq)

        aln = self.Class(data=[("a", dna), ("b", dna)])
        expect = self.Class(
            data=[("a", raw_ungapped), ("b", raw_ungapped)]).to_fasta()
        self.assertEqual(aln.degap().to_fasta(), expect)
        seqs = self.Class(data=[("a", dna), ("b", dna)])
        self.assertEqual(seqs.degap().to_fasta(), expect)

    def test_pad_seqs(self):
        """SequenceCollection pad_seqs should work on alignment."""
        # pad to max length
        padded1 = self.ragged_padded.pad_seqs()
        seqs1 = list(padded1.iter_seqs(seq_order=['a', 'b', 'c']))
        self.assertEqual(list(map(str, seqs1)), ['AAAAAA', 'AAA---', 'AAAA--'])

        # pad to alternate length
        padded1 = self.ragged_padded.pad_seqs(pad_length=10)
        seqs1 = list(padded1.iter_seqs(seq_order=['a', 'b', 'c']))
        self.assertEqual(list(map(str, seqs1)), ['AAAAAA----', 'AAA-------',
                                               'AAAA------'])

        # assertRaises error when pad_length is less than max seq length
        self.assertRaises(ValueError, self.ragged_padded.pad_seqs, 5)


class SequenceCollectionTests(SequenceCollectionBaseTests, TestCase):
    """Tests of the SequenceCollection object. Includes ragged collection tests.

    Should not test alignment-specific features.
    """

    def setUp(self):
        """Adds self.ragged for ragged collection tests."""
        self.ragged = SequenceCollection(
            {'a': 'AAAAAA', 'b': 'AAA', 'c': 'AAAA'})
        super(SequenceCollectionTests, self).setUp()

    def test_seq_len_get_ragged(self):
        """SequenceCollection seq_len get should work for ragged seqs"""
        self.assertEqual(self.ragged.seq_len, 6)

    def test_is_ragged_ragged(self):
        """SequenceCollection is_ragged should return True if ragged"""
        self.assertTrue(self.ragged.is_ragged())

    def test_Seqs_ragged(self):
        """SequenceCollection seqs should work on ragged alignment"""
        self.ragged.names = 'bac'
        self.assertEqual(list(self.ragged.seqs), ['AAA', 'AAAAAA', 'AAAA'])

    def test_iter_seqs_ragged(self):
        """SequenceCollection iter_seqs() method should support reordering of seqs"""
        self.ragged.names = ['a', 'b', 'c']
        seqs = list(self.ragged.iter_seqs())
        self.assertEqual(seqs, ['AAAAAA', 'AAA', 'AAAA'])
        seqs = list(self.ragged.iter_seqs(seq_order=['b', 'a', 'a']))
        self.assertEqual(seqs, ['AAA', 'AAAAAA', 'AAAAAA'])
        self.assertSameObj(seqs[1], seqs[2])
        self.assertSameObj(seqs[0], self.ragged.named_seqs['b'])

    def test_toPHYLIP_ragged(self):
        """SequenceCollection should refuse to convert ragged seqs to phylip"""
        align_rag = self.Class(['ACDEFGHIKLMNPQRSTUVWY-',
                                 'ACDEFGHIKLMNPQRSUUVWF-',
                                 'ACDEFGHIKLMNPERSKUVWC-',
                                 'ACNEFGHIKLMNUVWP-',
                                 ])

        self.assertRaises(ValueError, align_rag.to_phylip)

    def test_pad_seqs_ragged(self):
        """SequenceCollection pad_seqs should work on ragged alignment."""
        # pad to max length
        padded1 = self.ragged.pad_seqs()
        seqs1 = list(padded1.iter_seqs(seq_order=['a', 'b', 'c']))
        self.assertEqual(list(map(str, seqs1)), ['AAAAAA', 'AAA---', 'AAAA--'])

        # pad to alternate length
        padded1 = self.ragged.pad_seqs(pad_length=10)
        seqs1 = list(padded1.iter_seqs(seq_order=['a', 'b', 'c']))
        self.assertEqual(list(map(str, seqs1)), ['AAAAAA----', 'AAA-------',
                                               'AAAA------'])

        # assertRaises error when pad_length is less than max seq length
        self.assertRaises(ValueError, self.ragged.pad_seqs, 5)


class AlignmentBaseTests(SequenceCollectionBaseTests):
    """Tests of basic Alignment functionality. All Alignments should pass these.

    Note that this is not a TestCase: need to subclass to test each specific
    type of Alignment. Override self.Constructor with your alignment class
    as a constructor.
    """

    def test_positions(self):
        """SequenceCollection positions property should iterate over positions, using self.names"""
        r = self.Class({'a': 'AAAAAA', 'b': 'AAA---', 'c': 'AAAA--'})
        r.names = ['a', 'b', 'c']
        self.assertEqual(list(r.positions), list(map(list,
                                                     ['AAA', 'AAA', 'AAA', 'A-A', 'A--', 'A--'])))

    def test_iter_positions(self):
        #"""SequenceCollection iter_positions() method should support reordering of #cols"""
        r = self.Class(self.ragged_padded.named_seqs, names=['c', 'b'])
        self.assertEqual(list(r.iter_positions(pos_order=[5, 1, 3])),
                         list(map(list, ['--', 'AA', 'A-'])))
        # reorder names
        r = self.Class(self.ragged_padded.named_seqs, names=['a', 'b', 'c'])
        cols = list(r.iter_positions())
        self.assertEqual(cols, list(
            map(list, ['AAA', 'AAA', 'AAA', 'A-A', 'A--', 'A--'])))

    
    def test_take_positions(self):
        """SequenceCollection take_positions should return new alignment w/ specified pos"""
        self.assertEqual(self.gaps.take_positions([5, 4, 0],
                                                 seq_constructor=coerce_to_string),
                         {'a': 'AAA', 'b': 'A-A', 'c': '--A'})
        self.assertTrue(isinstance(self.gaps.take_positions([0]),
                                   SequenceCollection))
        # should be able to negate
        self.assertEqual(self.gaps.take_positions([5, 4, 0], negate=True,
                                                 seq_constructor=coerce_to_string),
                         {'a': 'AAAA', 'b': '--AA', 'c': 'A---'})

    def test_get_position_indices(self):
        """SequenceCollection get_position_indices should return names of cols where f(col)"""
        gap_1st = lambda x: x[0] == '-'
        gap_2nd = lambda x: x[1] == '-'
        gap_3rd = lambda x: x[2] == '-'
        is_list = lambda x: isinstance(x, list)
        self.gaps = self.Class(self.gaps.named_seqs, names=['a', 'b', 'c'])

        self.assertEqual(self.gaps.get_position_indices(gap_1st), [])
        self.assertEqual(self.gaps.get_position_indices(gap_2nd), [1, 2, 4])
        self.assertEqual(self.gaps.get_position_indices(
            gap_3rd), [2, 3, 4, 5, 6])
        self.assertEqual(self.gaps.get_position_indices(
            is_list), [0, 1, 2, 3, 4, 5, 6])
        # should be able to negate
        self.assertEqual(self.gaps.get_position_indices(gap_2nd, negate=True),
                         [0, 3, 5, 6])
        self.assertEqual(self.gaps.get_position_indices(gap_1st, negate=True),
                         [0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(self.gaps.get_position_indices(
            is_list, negate=True), [])

    def test_take_positions_if(self):
        """SequenceCollection take_positions_if should return cols where f(col) is True"""
        gap_1st = lambda x: x[0] == '-'
        gap_2nd = lambda x: x[1] == '-'
        gap_3rd = lambda x: x[2] == '-'
        is_list = lambda x: isinstance(x, list)
        self.gaps.names = 'abc'

        self.assertEqual(self.gaps.take_positions_if(gap_1st, seq_constructor=coerce_to_string),
                         {'a': '', 'b': '', 'c': ''})
        self.assertEqual(self.gaps.take_positions_if(gap_2nd, seq_constructor=coerce_to_string),
                         {'a': 'AAA', 'b': '---', 'c': 'A--'})
        self.assertEqual(self.gaps.take_positions_if(gap_3rd, seq_constructor=coerce_to_string),
                         {'a': 'AAAAA', 'b': '-A-AA', 'c': '-----'})
        self.assertEqual(self.gaps.take_positions_if(is_list, seq_constructor=coerce_to_string),
                         self.gaps)

        self.assertTrue(isinstance(self.gaps.take_positions_if(gap_1st),
                                   SequenceCollection))
        # should be able to negate
        self.assertEqual(self.gaps.take_positions_if(gap_1st, seq_constructor=coerce_to_string,
                                                   negate=True), self.gaps)
        self.assertEqual(self.gaps.take_positions_if(gap_2nd, seq_constructor=coerce_to_string,
                                                   negate=True), {'a': 'AAAA', 'b': 'AAAA', 'c': 'A---'})
        self.assertEqual(self.gaps.take_positions_if(gap_3rd, seq_constructor=coerce_to_string,
                                                   negate=True), {'a': 'AA', 'b': 'A-', 'c': 'AA'})

    
    def test_no_degenerates(self):
        """no_degenerates correctly excludes columns containing IUPAC ambiguity codes"""
        data = {'s1': 'AAA CCC GGG TTT'.replace(' ', ''),
                's2': 'CCC GGG T-T AAA'.replace(' ', ''),
                's3': 'GGR YTT AAA CCC'.replace(' ', '')}
        aln = self.Class(data=data, moltype=DNA)
        
        # motif length of 1, defaults - no gaps allowed
        result = aln.no_degenerates().todict()
        expect = {'s1': 'AA CC GG TTT'.replace(' ', ''),
                  's2': 'CC GG TT AAA'.replace(' ', ''),
                  's3': 'GG TT AA CCC'.replace(' ', '')}
        self.assertEqual(result, expect)
    
        # allow gaps
        result = aln.no_degenerates(allow_gap=True).todict()
        expect = {'s1': 'AA CC GGG TTT'.replace(' ', ''),
                  's2': 'CC GG T-T AAA'.replace(' ', ''),
                  's3': 'GG TT AAA CCC'.replace(' ', '')}
        self.assertEqual(result, expect)
    
        # motif length of 3, defaults - no gaps allowed
        result = aln.no_degenerates(motif_length=3).todict()
        expect = {'s1': 'TTT'.replace(' ', ''),
                  's2': 'AAA'.replace(' ', ''),
                  's3': 'CCC'.replace(' ', '')}
        self.assertEqual(result, expect)
    
        # allow gaps
        result = aln.no_degenerates(motif_length=3, allow_gap=True).todict()
        expect = {'s1': 'GGG TTT'.replace(' ', ''),
                  's2': 'T-T AAA'.replace(' ', ''),
                  's3': 'AAA CCC'.replace(' ', '')}
        self.assertEqual(result, expect)
    
    
    def test_omit_gap_pos(self):
        """SequenceCollection omit_gap_pos should return alignment w/o positions of gaps"""
        aln = self.end_gaps
        # first, check behavior when we're just acting on the cols (and not
        # trying to delete the naughty seqs).

        # default should strip out cols that are 100% gaps
        result = aln.omit_gap_pos(seq_constructor=coerce_to_string)
        self.assertEqual(result.todict(),
                         {'a': '-ABC', 'b': 'CBA-', 'c': '-DEF'})
        # if allowed_gap_frac is 1, shouldn't delete anything
        self.assertEqual(aln.omit_gap_pos(1, seq_constructor=coerce_to_string).todict(),
                         {'a': '--A-BC-', 'b': '-CB-A--', 'c': '--D-EF-'})
        # if allowed_gap_frac is 0, should strip out any cols containing gaps
        self.assertEqual(aln.omit_gap_pos(0, seq_constructor=coerce_to_string).todict(),
                         {'a': 'AB', 'b': 'BA', 'c': 'DE'})
        # intermediate numbers should work as expected
        self.assertEqual(aln.omit_gap_pos(0.4, seq_constructor=coerce_to_string).todict(),
                         {'a': 'ABC', 'b': 'BA-', 'c': 'DEF'})
        self.assertEqual(aln.omit_gap_pos(0.7, seq_constructor=coerce_to_string).todict(),
                         {'a': '-ABC', 'b': 'CBA-', 'c': '-DEF'})

        # when we increase the number of sequences to 6, more differences
        # start to appear.
        new_aln_data = aln.named_seqs.copy()
        new_aln_data['d'] = '-------'
        new_aln_data['e'] = 'XYZXYZX'
        new_aln_data['f'] = 'AB-CDEF'
        aln = self.Class(new_aln_data)
        
        # if no gaps are allowed, we get None
        self.assertEqual(aln.omit_gap_pos(0), None)
    
    def test_omit_bad_seqs(self):
        """omit_bad_seqs should return alignment w/o seqs causing most gaps"""
        data = {'s1': '-ACC--TT',
                's2': '-ACC--TT',
                's3': '-ACC--TT',
                's4': 'AACCGGTT',
                's5': 'AACCGGTT',
                's6': '--------'}
        
        aln = self.Class(data, moltype=DNA)
        # with defaults, excludes the fully gapped seq
        result = aln.omit_bad_seqs()
        self.assertEqual(result.todict(),
                         {'s1': '-ACC--TT',
                          's2': '-ACC--TT',
                          's3': '-ACC--TT',
                          's4': 'AACCGGTT',
                          's5': 'AACCGGTT'})
        # unless exclude_just_gap=False, which should just return self
        result = aln.omit_bad_seqs(exclude_just_gap=False)
        self.assertEqual(result.todict(), data)
        self.assertEqual(id(result), id(aln))
        
        # with disallowed_frac=0.6, we should drop s4&5 too
        result = aln.omit_bad_seqs(disallowed_frac=0.5)
        self.assertEqual(result.todict(),
                         {'s1': '-ACC--TT',
                          's2': '-ACC--TT',
                          's3': '-ACC--TT'})


    def test_matching_ref(self):
        """Alignment.matching_ref returns new aln with well-aln to temp"""
        aln = self.omitSeqsTemplate_aln
        result = aln.matching_ref('s3', 0.9, 5)
        self.assertEqual(result, {'s3': 'UUCCUUCUU-UUC',
                                  's4': 'UU-UUUU-UUUUC'})
        result2 = aln.matching_ref('s4', 0.9, 4)
        self.assertEqual(result2, {'s3': 'UUCCUUCUU-UUC',
                                   's4': 'UU-UUUU-UUUUC'})
        result3 = aln.matching_ref('s1', 0.9, 4)
        self.assertEqual(result3, {'s2': 'UC------U---C',
                                   's1': 'UC-----CU---C', 's5': '-------------'})
        result4 = aln.matching_ref('s3', 0.5, 13)
        self.assertEqual(result4, {'s3': 'UUCCUUCUU-UUC',
                                   's4': 'UU-UUUU-UUUUC'})

    
    def test_iupac_consensus_RNA(self):
        """SequenceCollection iupac_consensus should use RNA IUPAC symbols correctly"""
        alignmentUpper = self.Class(['UCAGN-UCAGN-UCAGN-UCAGAGCAUN-',
                                      'UUCCAAGGNN--UUCCAAGGNNAGCAG--',
                                      'UUCCAAGGNN--UUCCAAGGNNAGCUA--',
                                      'UUUUCCCCAAAAGGGGNNNN--AGCUA--',
                                      'UUUUCCCCAAAAGGGGNNNN--AGCUA--',
                                      ], moltype=RNA)

        # following IUPAC consensus calculated by hand
        # Test all uppper
        self.assertEqual(alignmentUpper.iupac_consensus(),
                         'UYHBN?BSNN??KBVSN?NN??AGCWD?-')

    def test_iupac_consensus_DNA(self):
        """SequenceCollection iupac_consensus should use DNA IUPAC symbols correctly"""
        alignmentUpper = self.Class(['TCAGN-TCAGN-TCAGN-TCAGAGCATN-',
                                      'TTCCAAGGNN--TTCCAAGGNNAGCAG--',
                                      'TTCCAAGGNN--TTCCAAGGNNAGCTA--',
                                      'TTTTCCCCAAAAGGGGNNNN--AGCTA--',
                                      'TTTTCCCCAAAAGGGGNNNN--AGCTA--',
                                      ])
        # following IUPAC consensus calculated by hand
        # Test all uppper
        self.assertEqual(alignmentUpper.iupac_consensus(DNA),
                         'TYHBN?BSNN??KBVSN?NN??AGCWD?-')

    def test_iupac_consensus_Protein(self):
        """SequenceCollection iupac_consensus should use protein IUPAC symbols correctly"""
        alignmentUpper = self.Class(['ACDEFGHIKLMNPQRSTUVWY-',
                                      'ACDEFGHIKLMNPQRSUUVWF-',
                                      'ACDEFGHIKLMNPERSKUVWC-',
                                      'ACNEFGHIKLMNPQRS-UVWP-',
                                      ])
        # following IUPAC consensus calculated by hand
        # Test all uppper
        self.assertEqual(alignmentUpper.iupac_consensus(PROTEIN),
                         'ACBEFGHIKLMNPZRS?UVWX-')

    def test_is_ragged(self):
        """SequenceCollection is_ragged should return true if ragged alignment"""
        assert(not self.identical.is_ragged())
        assert(not self.gaps.is_ragged())

    def test_column_probs(self):
        """SequenceCollection.column_probs should find Pr(symbol) in each column"""
        # make an alignment with 4 seqs (easy to calculate probabilities)
        align = self.Class(["AAA", "ACA", "GGG", "GUC"])
        cp = align.column_probs()
        # check that the column probs match the counts we expect
        self.assertEqual(cp, list(map(Freqs, [
            {'A': 0.5, 'G': 0.5},
            {'A': 0.25, 'C': 0.25, 'G': 0.25, 'U': 0.25},
            {'A': 0.5, 'G': 0.25, 'C': 0.25},
        ])))

    def test_majority_consensus(self):
        """SequenceCollection.majority_consensus should return commonest symbol per column"""
        # Check the exact strings expected from string transform
        self.assertEqual(self.sequences.majority_consensus(str), 'UCAG')

    def test_uncertainties(self):
        """SequenceCollection.uncertainties should match hand-calculated values"""
        aln = self.Class(['ABC', 'AXC'])
        obs = aln.uncertainties()
        self.assertFloatEqual(obs, [0, 1, 0])
        # check what happens with only one input sequence
        aln = self.Class(['ABC'])
        obs = aln.uncertainties()
        self.assertFloatEqual(obs, [0, 0, 0])
        # check that we can screen out bad items OK
        aln = self.Class(['ABC', 'DEF', 'GHI', 'JKL', '333'], moltype=BYTES)
        obs = aln.uncertainties('ABCDEFGHIJKLMNOP')
        self.assertFloatEqual(obs, [2.0] * 3)

    def test_column_freqs(self):
        """Alignment.column_freqs should count symbols in each column"""
        # calculate by hand what the first and last positions should look like in
        # each case
        firstvalues = [
            [self.sequences, Freqs('UUU')],
            ]

        lastvalues = [
            [self.sequences, Freqs('GGG')]
            ]
        # check that the first positions are what we expected
        for obj, result in firstvalues:
            freqs = obj.column_freqs()
            self.assertEqual(str(freqs[0]), str(result))
        # check that the last positions are what we expected
        for obj, result in lastvalues:
            freqs = obj.column_freqs()
            self.assertEqual(str(freqs[-1]), str(result))

    def test_get_pssm(self):
        """Alignment get_pssm should produce position specific score matrix."""
        get_pssm = {
            0: {'A': 1.0, 'C': 1.0, 'U': 5.0},
            1: {'C': 6.0, 'U': 1.0},
            2: {'A': 3.0, 'C': 2.0, 'G': 2.0},
            3: {'A': 3.0, 'G': 4.0},
            4: {'C': 1.0, 'G': 1.0, 'U': 5.0},
            5: {'C': 6.0, 'U': 1.0},
            6: {'A': 3.0, 'G': 4.0},
            7: {'A': 1.0, 'G': 6.0},
            8: {'A': 1.0, 'C': 1.0, 'G': 1.0, 'U': 4.0},
            9: {'A': 1.0, 'C': 2.0, 'U': 4.0},
        }
        self.assertEqual(self.many.get_pssm(), get_pssm)

    def test_sample(self):
        """Alignment.sample should permute alignment by default"""
        alignment = self.Class({'seq1': 'ABCDEFGHIJKLMNOP',
                                'seq2': 'ABCDEFGHIJKLMNOP'})
        # effectively permute columns, preserving length
        shuffled = alignment.sample()
        # ensure length correct
        sample = alignment.sample(10)
        self.assertEqual(len(sample), 10)
        # test columns alignment preserved
        seqs = list(sample.todict().values())
        self.assertEqual(seqs[0], seqs[1])
        # ensure each char occurs once as sampling without replacement
        for char in seqs[0]:
            self.assertEqual(seqs[0].count(char), 1)

    def test_sample_with_replacement(self):
        # test with replacement -- just verify that it rnus
        alignment = self.Class({'seq1': 'gatc', 'seq2': 'gatc'})
        sample = alignment.sample(1000, with_replacement=True)
        self.assertEqual(len(sample), 1000)
        # ensure that sampling with replacement works on single col alignment
        alignment1 = self.Class({'seq1': 'A',
                                 'seq2': 'A'})
        result = alignment1.sample(with_replacement=True)
        self.assertEqual(len(result), 1)

    def test_sample_tuples(self):
        ##### test with motif size != 1 #####
        alignment = self.Class({'seq1': 'AABBCCDDEEFFGGHHIIJJKKLLMMNNOOPP',
                                'seq2': 'AABBCCDDEEFFGGHHIIJJKKLLMMNNOOPP'})
        shuffled = alignment.sample(motif_length=2)
        # ensure length correct
        sample = alignment.sample(10, motif_length=2)
        self.assertEqual(len(sample), 20)
        # test columns alignment preserved
        seqs = list(sample.todict().values())
        self.assertEqual(seqs[0], seqs[1])
        # ensure each char occurs twice as sampling dinucs without replacement
        for char in seqs[0]:
            self.assertEqual(seqs[0].count(char), 2)

    def test_copy(self):
        """correctly copy an alignment"""
        aln = self.Class(data=[('a', 'AC-GT'), ('b', 'ACCGT')])
        copied = aln.copy()
        self.assertTrue(type(aln), type(copied))
        self.assertEqual(aln.todict(), copied.todict())
        self.assertEqual(id(aln.moltype), id(copied.moltype))
        aln = self.Class(data=[('a', 'AC-GT'), ('b', 'ACCGT')],
                         info={'check': True})
        copied = aln.copy()
        self.assertEqual(aln.info, copied.info)

    def test_to_pretty(self):
        """produce correct pretty print formatted text"""
        seqs = {'seq1': 'ACGAANGA',
                'seq2': '-CGAACGA',
                'seq3': 'ATGAACGA'}
        expect = ["seq1    ACGAANGA",
                  "seq2    -....C..",
                  "seq3    .T...C.."]

        aln = self.Class(data=seqs, moltype=DNA)
        got = aln.to_pretty(name_order=['seq1', 'seq2', 'seq3'])
        self.assertEqual(got, '\n'.join(expect))

        got = aln.to_pretty(
            name_order=['seq1', 'seq2', 'seq3'], interleave_len=4)
        expect = ["seq1    ACGA",
                  "seq2    -...",
                  "seq3    .T..",
                  "",
                  "seq1    ANGA",
                  "seq2    .C..",
                  "seq3    .C.."]
        self.assertEqual(got, '\n'.join(expect))
    
    def test_variable_positions(self):
        """correctly identify variable positions"""
        new_seqs = {'seq1': 'ACGTACGT',
                    'seq2': 'ACCGACGT',
                    'seq3': 'ACGTACGT'}
        aln = self.Class(data=new_seqs, moltype=DNA)
        self.assertEqual(aln.variable_positions(), [2, 3])
    
    def test_to_type(self):
        """correctly interconvert between alignment types"""
        new_seqs = {'seq1': 'ACGTACGTA',
                    'seq2': 'ACCGAA---',
                    'seq3': 'ACGTACGTT'}
        array_align = self.Class == ArrayAlignment
        # when array_align arg matches instance class, no conversion
        # and get back self
        aln = self.Class(data=new_seqs)
        new = aln.to_type(array_align=array_align)
        self.assertEqual(id(aln), id(new))
        
        # when array_align arg does not match, should get back the opposite type
        new = aln.to_type(array_align=not array_align)
        self.assertFalse(isinstance(new, self.Class))
        
        # we should be able to specify moltype and alignment
        new = aln.to_type(array_align=not array_align, moltype=DNA)
        self.assertEqual(new.todict(), new_seqs)
        # and translate
        self.assertEqual(new.get_translation().todict(),
                         {'seq1': 'TYV', 'seq3': 'TYV', 'seq2': 'TE-'})
    
    def test_replace_seqs(self):
        """replace_seqs should replace 1-letter w/ 3-letter seqs"""
        a = self.Class({'seq1': 'ACGU', 'seq2': 'C-UA', 'seq3': 'C---'})
        seqs = {'seq1': 'AAACCCGGGUUU', 'seq2': 'CCCUUUAAA', 'seq3': 'CCC'}
        result = a.replace_seqs(seqs)  # default behaviour
        self.assertEqual(result.to_fasta(),
                         ">seq1\nAAACCCGGGUUU\n>seq2\nCCC---UUUAAA\n>seq3\nCCC---------")

        result = a.replace_seqs(seqs, aa_to_codon=True)  # default behaviour
        self.assertEqual(result.to_fasta(),
                         ">seq1\nAAACCCGGGUUU\n>seq2\nCCC---UUUAAA\n>seq3\nCCC---------")

        # should correctly gap the same sequences with same length
        result = a.replace_seqs(
            a.degap(), aa_to_codon=False)  # default behaviour
        self.assertEqual(result.todict(),
                         {'seq1': 'ACGU', 'seq2': 'C-UA', 'seq3': 'C---'})

        # should fail when not same length if aa_to_codon is False
        new = SequenceCollection([(n, s.replace('-', ''))
                                  for n, s in list(a[:3].todict().items())])
        self.assertRaises(ValueError,
                          a.replace_seqs, new, aa_to_codon=False)

        # check the gaps are changed
        aln1 = self.Class(data={'a': 'AC-CT', 'b': 'ACGCT'})
        aln2 = self.Class(data={'a': 'ACC-T', 'b': 'ACGCT'})

        result = aln1.replace_seqs(aln2, aa_to_codon=False)
        self.assertTrue(id(aln1) != id(aln2))
        self.assertEqual(aln1.todict(), result.todict())
        

class ArrayAlignmentTests(AlignmentBaseTests, TestCase):
    Class = ArrayAlignment

    def test_slice_align(self):
        """slicing alignment should work correctly"""
        data = {'seq1': 'ACGACGACG',
                'seq2': 'ACGACGACG',
                'seq3': 'ACGACGACG'}
        alignment = self.Class(data=data)
        sub_align = alignment[2:5]
        self.assertTrue(isinstance(sub_align, self.Class))
        expect = {'seq1': 'GAC',
                  'seq2': 'GAC',
                  'seq3': 'GAC'}
        self.assertEqual(sub_align.todict(), expect)
        # slice third positions
        sub_align = alignment[2::3]
        expect = {'seq1': 'GGG',
                  'seq2': 'GGG',
                  'seq3': 'GGG'}
        self.assertEqual(sub_align.todict(), expect)
    
    def test_get_freqs(self):
        """ArrayAlignment get_seq_freqs: should work on positions and sequences 
        """
        s1 = DNA.make_seq('TCAG', name='s1')
        s2 = DNA.make_seq('CCAC', name='s2')
        s3 = DNA.make_seq('AGAT', name='s3')
        da = ArrayAlignment([s1, s2, s3], moltype=DNA, alphabet=DNA.alphabet)
        seq_exp = array([[1, 1, 1, 1], [0, 3, 1, 0], [1, 0, 2, 1]])
        pos_exp = array([[1, 1, 1, 0], [0, 2, 0, 1],
                        [0, 0, 3, 0], [1, 1, 0, 1]])
        self.assertEqual(da._get_freqs(index=1), pos_exp)
        self.assertEqual(da._get_freqs(index=0), seq_exp)

    def test_get_seq_freqs(self):
        """ArrayAlignment get_seq_freqs: should work with DnaSequences and strings
        """
        exp = array([[1, 1, 1, 1], [0, 3, 1, 0], [1, 0, 2, 1]])

        s1 = DNA.make_seq('TCAG', name='s1')
        s2 = DNA.make_seq('CCAC', name='s2')
        s3 = DNA.make_seq('AGAT', name='s3')
        da = ArrayAlignment([s1, s2, s3], moltype=DNA, alphabet=DNA.alphabet)
        obs = da.get_seq_freqs()
        self.assertEqual(obs.Data, exp)
        self.assertEqual(obs.alphabet, DNA.alphabet)
        self.assertEqual(obs.char_order, list("TCAG"))

        s1 = 'TCAG'
        s2 = 'CCAC'
        s3 = 'AGAT'
        da = ArrayAlignment([s1, s2, s3], moltype=DNA, alphabet=DNA.alphabet)
        obs = da.get_seq_freqs()
        self.assertEqual(obs.Data, exp)
        self.assertEqual(obs.alphabet, DNA.alphabet)
        self.assertEqual(obs.char_order, list("TCAG"))

    def test_get_pos_freqs_sequence(self):
        """ArrayAlignment get_pos_freqs: should work with DnaSequences and strings
        """
        exp = array([[1, 1, 1, 0], [0, 2, 0, 1], [0, 0, 3, 0], [1, 1, 0, 1]])

        s1 = DNA.make_seq('TCAG', name='s1')
        s2 = DNA.make_seq('CCAC', name='s2')
        s3 = DNA.make_seq('AGAT', name='s3')
        da = ArrayAlignment([s1, s2, s3], moltype=DNA, alphabet=DNA.alphabet)
        obs = da.get_pos_freqs()
        self.assertEqual(obs.Data, exp)
        self.assertEqual(obs.alphabet, DNA.alphabet)
        self.assertEqual(obs.char_order, list("TCAG"))

        s1 = 'TCAG'
        s2 = 'CCAC'
        s3 = 'AGAT'
        da = ArrayAlignment([s1, s2, s3], moltype=DNA, alphabet=DNA.alphabet)
        obs = da.get_pos_freqs()
        self.assertEqual(obs.Data, exp)
        self.assertEqual(obs.alphabet, DNA.alphabet)
        self.assertEqual(obs.char_order, list("TCAG"))


class AlignmentTests(AlignmentBaseTests, TestCase):
    Class = Alignment

    def test_get_freqs(self):
        """Alignment _get_freqs: should work on positions and sequences 
        """
        s1 = DNA.make_seq('TCAG', name='s1')
        s2 = DNA.make_seq('CCAC', name='s2')
        s3 = DNA.make_seq('AGAT', name='s3')
        aln = Alignment([s1, s2, s3], moltype=DNA, alphabet=DNA.alphabet)
        seq_exp = array([[1, 1, 1, 1], [0, 3, 1, 0], [1, 0, 2, 1]])
        pos_exp = array([[1, 1, 1, 0], [0, 2, 0, 1],
                        [0, 0, 3, 0], [1, 1, 0, 1]])
        self.assertEqual(aln._get_freqs(index=1), pos_exp)
        self.assertEqual(aln._get_freqs(index=0), seq_exp)

    def test_get_seq_freqs(self):
        """Alignment get_seq_freqs: should work with DnaSequences and strings
        """
        exp = array([[1, 1, 1, 1], [0, 3, 1, 0], [1, 0, 2, 1]])

        s1 = DNA.make_seq('TCAG', name='s1')
        s2 = DNA.make_seq('CCAC', name='s2')
        s3 = DNA.make_seq('AGAT', name='s3')
        aln = Alignment([s1, s2, s3], moltype=DNA, alphabet=DNA.alphabet)
        obs = aln.get_seq_freqs()
        self.assertEqual(obs.Data, exp)
        self.assertEqual(obs.alphabet, DNA.alphabet)
        self.assertEqual(obs.char_order, list("TCAG"))

        s1 = 'TCAG'
        s2 = 'CCAC'
        s3 = 'AGAT'
        aln = Alignment([s1, s2, s3], moltype=DNA, alphabet=DNA.alphabet)
        obs = aln.get_seq_freqs()
        self.assertEqual(obs.Data, exp)
        self.assertEqual(obs.alphabet, DNA.alphabet)
        self.assertEqual(obs.char_order, list("TCAG"))

    def test_get_pos_freqs(self):
        """Alignment get_pos_freqs: should work with DnaSequences and strings
        """
        exp = array([[1, 1, 1, 0], [0, 2, 0, 1], [0, 0, 3, 0], [1, 1, 0, 1]])

        s1 = DNA.make_seq('TCAG', name='s1')
        s2 = DNA.make_seq('CCAC', name='s2')
        s3 = DNA.make_seq('AGAT', name='s3')
        aln = Alignment([s1, s2, s3], moltype=DNA, alphabet=DNA.alphabet)
        obs = aln.get_pos_freqs()
        self.assertEqual(obs.Data, exp)
        self.assertEqual(obs.alphabet, DNA.alphabet)
        self.assertEqual(obs.char_order, list("TCAG"))

        s1 = 'TCAG'
        s2 = 'CCAC'
        s3 = 'AGAT'
        aln = Alignment([s1, s2, s3], moltype=DNA, alphabet=DNA.alphabet)
        obs = aln.get_pos_freqs()
        self.assertEqual(obs.Data, exp)
        self.assertEqual(obs.alphabet, DNA.alphabet)
        self.assertEqual(obs.char_order, list("TCAG"))

    def make_and_filter(self, raw, expected, motif_length):
        # a simple filter func
        func = lambda x: re.findall("[-N?]", " ".join(x)) == []
        aln = self.Class(raw)
        result = aln.filtered(
            func, motif_length=motif_length, log_warnings=False)
        self.assertEqual(result.todict(), expected)

    def test_filtered(self):
        """filtered should return new alignment with positions consistent with
        provided callback function"""
        # a simple filter option
        raw = {'a': 'ACGACGACG',
               'b': 'CCC---CCC',
               'c': 'AAAA--AAA'}
        self.make_and_filter(
            raw, {'a': 'ACGACG', 'b': 'CCCCCC', 'c': 'AAAAAA'}, 1)
        # check with motif_length = 2
        self.make_and_filter(raw, {'a': 'ACAC', 'b': 'CCCC', 'c': 'AAAA'}, 2)
        # check with motif_length = 3
        self.make_and_filter(
            raw, {'a': 'ACGACG', 'b': 'CCCCCC', 'c': 'AAAAAA'}, 3)

    def test_sliding_windows(self):
        """sliding_windows should return slices of alignments."""
        alignment = self.Class(
            {'seq1': 'ACGTACGT', 'seq2': 'ACGTACGT', 'seq3': 'ACGTACGT'})
        result = []
        for bit in alignment.sliding_windows(5, 2):
            result += [bit]
        self.assertEqual(result[0].todict(), {
                         'seq3': 'ACGTA', 'seq2': 'ACGTA', 'seq1': 'ACGTA'})
        self.assertEqual(result[1].todict(), {
                         'seq3': 'GTACG', 'seq2': 'GTACG', 'seq1': 'GTACG'})

        result = []
        for bit in alignment.sliding_windows(5, 1):
            result += [bit]
        self.assertEqual(result[0].todict(), {
                         'seq3': 'ACGTA', 'seq2': 'ACGTA', 'seq1': 'ACGTA'})
        self.assertEqual(result[1].todict(), {
                         'seq3': 'CGTAC', 'seq2': 'CGTAC', 'seq1': 'CGTAC'})
        self.assertEqual(result[2].todict(), {
                         'seq3': 'GTACG', 'seq2': 'GTACG', 'seq1': 'GTACG'})
        self.assertEqual(result[3].todict(), {
                         'seq3': 'TACGT', 'seq2': 'TACGT', 'seq1': 'TACGT'})

    def test_with_gaps_from(self):
        """with_gaps_from should overwrite with gaps."""
        gapless = self.Class({'seq1': 'TCG', 'seq2': 'TCG'})
        pregapped = self.Class({'seq1': '-CG', 'seq2': 'TCG'})
        template = self.Class({'seq1': 'A-?', 'seq2': 'ACG'})
        r1 = gapless.with_gaps_from(template).todict()
        r2 = pregapped.with_gaps_from(template).todict()
        self.assertEqual(r1, {'seq1': 'T-G', 'seq2': 'TCG'})
        self.assertEqual(r2, {'seq1': '--G', 'seq2': 'TCG'})

    def test_get_degapped_relative_to(self):
        """should remove all columns with a gap in sequence with given name"""
        aln = self.Class([
            ['name1', '-AC-DEFGHI---'],
            ['name2', 'XXXXXX--XXXXX'],
            ['name3', 'YYYY-YYYYYYYY'],
            ['name4', '-KL---MNPR---'],
            ])
        out_aln = self.Class([
            ['name1', 'ACDEFGHI'],
            ['name2', 'XXXX--XX'],
            ['name3', 'YY-YYYYY'],
            ['name4', 'KL--MNPR'],
            ])
        self.assertEqual(aln.get_degapped_relative_to('name1'), out_aln)

        self.assertRaises(ValueError, aln.get_degapped_relative_to, 'nameX')

    def test_add_from_ref_aln(self):
        """should add or insert seqs based on align to reference"""
        aln1 = self.Class([
            ['name1', '-AC-DEFGHI---'],
            ['name2', 'XXXXXX--XXXXX'],
            ['name3', 'YYYY-YYYYYYYY'],
            ])

        aln2 = self.Class([
            ['name1', 'ACDEFGHI'],
            ['name4', 'KL--MNPR'],
            ['name5', 'KLACMNPR'],
            ['name6', 'KL--MNPR'],
            ])

        aligned_to_ref_out_aln_inserted = self.Class([
            ['name1', '-AC-DEFGHI---'],
            ['name4', '-KL---MNPR---'],
            ['name5', '-KL-ACMNPR---'],
            ['name6', '-KL---MNPR---'],
            ['name2', 'XXXXXX--XXXXX'],
            ['name3', 'YYYY-YYYYYYYY'],
            ])

        aln2_wrong_refseq = self.Class((
            ('name1', 'ACDXFGHI'),
            ('name4', 'KL--MNPR'),
            ))

        aln2_wrong_refseq_name = self.Class([
            ['nameY', 'ACDEFGHI'],
            ['name4', 'KL--MNPR'],
            ])

        aln2_different_aln_class = ArrayAlignment([
            ['name1', 'ACDEFGHI'],
            ['name4', 'KL--MNPR'],
            ])

        aln2_list = [
            ['name1', 'ACDEFGHI'],
            ['name4', 'KL--MNPR'],
            ]

        aligned_to_ref_out_aln = self.Class([
            ['name1', '-AC-DEFGHI---'],
            ['name2', 'XXXXXX--XXXXX'],
            ['name3', 'YYYY-YYYYYYYY'],
            ['name4', '-KL---MNPR---'],
            ])

        out_aln = aln1.add_from_ref_aln(aln2, after_name='name1')
        self.assertEqual(str(aligned_to_ref_out_aln_inserted),
                         str(out_aln))  # test insert_after

        out_aln = aln1.add_from_ref_aln(aln2, before_name='name2')
        self.assertEqual(aligned_to_ref_out_aln_inserted,
                         out_aln)  # test insert_before

        self.assertRaises(ValueError, aln1.add_from_ref_aln,
                          aln2_wrong_refseq_name)  # test wrong_refseq_name

        aln = aln1.add_from_ref_aln(aln2_different_aln_class)
        self.assertEqual(aligned_to_ref_out_aln,
                         aln)  # test_align_to_refseq_different_aln_class

        aln = aln1.add_from_ref_aln(aln2_list)
        self.assertEqual(aligned_to_ref_out_aln,
                         aln)  # test from_list

        self.assertRaises(ValueError, aln1.add_from_ref_aln,
                          aln2_wrong_refseq)  # test wrong_refseq


class ArrayAlignmentSpecificTests(TestCase):
    """Tests of the ArrayAlignment object and its methods"""

    def setUp(self):
        """Define some standard alignments."""
        self.a = ArrayAlignment(array([[0, 1, 2], [3, 4, 5]]),
                                conversion_f=aln_from_array)
        self.a2 = ArrayAlignment(['ABC', 'DEF'], names=['x', 'y'])

        class ABModelSequence(ArraySequence):
            alphabet = AB.alphabet
        self.ABModelSequence = ABModelSequence
        self.a = ArrayAlignment(list(map(ABModelSequence, ['abaa', 'abbb'])),
                                alphabet=AB.alphabet)
        self.b = Alignment(['ABC', 'DEF'])
        self.c = SequenceCollection(['ABC', 'DEF'])

    def test_init(self):
        """ArrayAlignment init should work from a sequence"""
        a = ArrayAlignment(array([[0, 1, 2], [3, 4, 5]]),
                           conversion_f=aln_from_array)
        self.assertEqual(a.seq_data, array([[0, 3], [1, 4], [2, 5]], 'B'))
        self.assertEqual(a.array_positions, array([[0, 1, 2], [3, 4, 5]], 'B'))
        self.assertEqual(a.names, ['seq_0', 'seq_1', 'seq_2'])

    def test_guess_input_type(self):
        """ArrayAlignment _guess_input_type should figure out data type correctly"""
        git = self.a._guess_input_type
        self.assertEqual(git(self.a), 'array_aln')
        self.assertEqual(git(self.b), 'aln')
        self.assertEqual(git(self.c), 'collection')
        self.assertEqual(git('>ab\nabc'), 'fasta')
        self.assertEqual(git(['>ab', 'abc']), 'fasta')
        self.assertEqual(git(['abc', 'def']), 'generic')
        # precedence over generic
        self.assertEqual(git([[1, 2], [4, 5]]), 'kv_pairs')
        self.assertEqual(git([[1, 2, 3], [4, 5, 6]]), 'generic')
        self.assertEqual(git([ArraySequence('abc')]), 'array_seqs')
        self.assertEqual(git(array([[1, 2, 3], [4, 5, 6]])), 'array')
        self.assertEqual(git({'a': 'aca'}), 'dict')
        self.assertEqual(git([]), 'empty')

    def test_init_seqs(self):
        """ArrayAlignment init should work from ArraySequence objects."""
        s = list(map(ArraySequence, ['abc', 'def']))
        a = ArrayAlignment(s)
        self.assertEqual(a.seq_data, array(['abc', 'def'], 'c').view('B'))

    def test_init_generic(self):
        """ArrayAlignment init should work from generic objects."""
        s = ['abc', 'def']
        a = ArrayAlignment(s)
        self.assertEqual(a.seq_data, array(['abc', 'def'], 'c').view('B'))

    def test_init_aln(self):
        """ArrayAlignment init should work from another alignment."""
        s = ['abc', 'def']
        a = ArrayAlignment(s)
        b = ArrayAlignment(a)
        self.assertNotSameObj(a.seq_data, b.seq_data)
        self.assertEqual(b.seq_data, array(['abc', 'def'], 'c').view('B'))

    def test_init_dict(self):
        """ArrayAlignment init should work from dict."""
        s = {'abc': 'AAACCC', 'xyz': 'GCGCGC'}
        a = ArrayAlignment(s, names=['abc', 'xyz'])
        self.assertEqual(a.seq_data, array(['AAACCC', 'GCGCGC'], 'c').view('B'))
        self.assertEqual(tuple(a.names), ('abc', 'xyz'))

    def test_init_empty(self):
        """ArrayAlignment init should fail if empty."""
        self.assertRaises(TypeError, ArrayAlignment)
        self.assertRaises(ValueError, ArrayAlignment, 3)

    def test_get_alphabet_and_moltype(self):
        """ArrayAlignment should figure out correct alphabet and moltype"""
        s1 = 'A'
        s2 = RNA.make_seq('AA')

        d = ArrayAlignment(s1)
        self.assertSameObj(d.moltype, BYTES)
        self.assertSameObj(d.alphabet, BYTES.alphabet)

        d = ArrayAlignment(s1, moltype=RNA)
        self.assertSameObj(d.moltype, RNA)
        self.assertSameObj(d.alphabet, RNA.alphabets.degen_gapped)

        d = ArrayAlignment(s1, alphabet=RNA.alphabet)
        self.assertSameObj(d.moltype, RNA)
        self.assertSameObj(d.alphabet, RNA.alphabet)

        d = ArrayAlignment(s2)
        self.assertSameObj(d.moltype, RNA)
        self.assertSameObj(d.alphabet, RNA.alphabets.degen_gapped)

        d = ArrayAlignment(s2, moltype=DNA)
        self.assertSameObj(d.moltype, DNA)
        self.assertSameObj(d.alphabet, DNA.alphabets.degen_gapped)
        # checks for containers
        d = ArrayAlignment([s2])
        self.assertSameObj(d.moltype, RNA)
        d = ArrayAlignment({'x': s2})
        self.assertSameObj(d.moltype, RNA)
        d = ArrayAlignment(set([s2]))
        self.assertSameObj(d.moltype, RNA)

    def test_iter(self):
        """ArrayAlignment iter should iterate over positions"""
        result = list(iter(self.a2))
        for i, j in zip(result, [list(i) for i in ['AD', 'BE', 'CF']]):
            self.assertEqual(i, j)

    def test_getitem(self):
        """ArrayAlignment getitem act like standard alignment slice"""
        a2 = self.a2
        expect = {'x': 'B', 'y': 'E'}
        got = a2[1]
        self.assertEqual(got.todict(), expect)
        expect = {'x': 'BC', 'y': 'EF'}
        got = a2[1:]
        self.assertEqual(got.todict(), expect)

    def test_get_sub_alignment(self):
        """ArrayAlignment get_sub_alignment should get requested part of alignment."""
        a = ArrayAlignment('>x ABCE >y FGHI >z JKLM'.split())
        # passing in positions should keep all seqs, but just selected
        # positions
        b = ArrayAlignment('>x BC >y GH >z KL'.split())
        a_1 = a.get_sub_alignment(pos=[1, 2])
        self.assertEqual(a_1.names, b.names)

        self.assertEqual(a_1.seqs, b.seqs)
        #...and with invert_pos, should keep all except the positions passed in
        a_2 = a.get_sub_alignment(pos=[0, 3], invert_pos=True)
        self.assertEqual(a_2.seqs, b.seqs)
        self.assertEqual(a_2.names, b.names)
        # passing in seqs should keep all positions, but just selected seqs
        c = ArrayAlignment('>x ABCE >z JKLM'.split())
        a_3 = a.get_sub_alignment(seqs=[0, 2])
        self.assertEqual(a_3.seqs, c.seqs)
        # check that labels were updates as well...
        self.assertEqual(a_3.names, c.names)
        #...and should work with invert_seqs to exclude just selected seqs
        a_4 = a.get_sub_alignment(seqs=[1], invert_seqs=True)
        self.assertEqual(a_4.seqs, c.seqs)
        self.assertEqual(a_4.names, c.names)
        # should be able to do both seqs and positions simultaneously
        d = ArrayAlignment('>x BC >z KL'.split())
        a_5 = a.get_sub_alignment(seqs=[0, 2], pos=[1, 2])
        self.assertEqual(a_5.seqs, d.seqs)
        self.assertEqual(a_5.names, d.names)

    def test_str(self):
        """ArrayAlignment str should return FASTA representation of aln"""
        self.assertEqual(str(self.a2), '>x\nABC\n>y\nDEF\n')
        # should work if labels diff length
        self.a2.names[-1] = 'yyy'
        self.assertEqual(str(self.a2), '>x\nABC\n>yyy\nDEF\n')

    def test_get_freqs(self):
        """ArrayAlignment _get_freqs should get row or col freqs"""
        ABModelSequence = self.ABModelSequence
        a = self.a
        self.assertEqual(a._get_freqs(0), array([[3, 1], [1, 3]]))
        self.assertEqual(a._get_freqs(1), array(
            [[2, 0], [0, 2], [1, 1], [1, 1]]))

    def test_get_seq_freqs(self):
        """ArrayAlignment get_seq_freqs should get profile of freqs in each seq"""
        ABModelSequence = self.ABModelSequence
        a = self.a
        f = a.get_seq_freqs()
        self.assertEqual(f.Data, array([[3, 1], [1, 3]]))

    def test_get_pos_freqs(self):
        """ArrayAlignment get_pos_freqs should get profile of freqs at each pos"""
        ABModelSequence = self.ABModelSequence
        a = self.a
        f = a.get_pos_freqs()
        self.assertEqual(f.Data, array([[2, 0], [0, 2], [1, 1], [1, 1]]))

    def test_get_seq_entropy(self):
        """ArrayAlignment get_seq_entropy should get entropy of each seq"""
        ABModelSequence = self.ABModelSequence
        a = ArrayAlignment(list(map(ABModelSequence, ['abab', 'bbbb', 'abbb'])),
                           alphabet=AB.alphabet)
        f = a.get_seq_entropy()
        e = 0.81127812445913283  # sum(p log_2 p) for p = 0.25, 0.75
        self.assertFloatEqual(f, array([1, 0, e]))

    def test_get_pos_entropy(self):
        """ArrayAlignment get_pos_entropy should get entropy of each pos"""
        ABModelSequence = self.ABModelSequence
        a = self.a
        f = a.get_pos_entropy()
        e = array([0, 0, 1, 1])
        self.assertEqual(f, e)


class IntegrationTests(TestCase):
    """Test for integration between regular and model seqs and alns"""

    def setUp(self):
        """Intialize some standard sequences"""
        self.r1 = RNA.make_seq('AAA', name='x')
        self.r2 = RNA.make_seq('CCC', name='y')
        self.m1 = RNA.make_array_seq('AAA', name='xx')
        self.m2 = RNA.make_array_seq('CCC', name='yy')

    def test_model_to_model(self):
        """Model seq should work with dense alignment"""
        a = ArrayAlignment([self.m1, self.m2])
        self.assertEqual(str(a), '>xx\nAAA\n>yy\nCCC\n')
        a = ArrayAlignment([self.m1, self.m2], moltype=DNA)
        self.assertEqual(str(a), '>xx\nAAA\n>yy\nCCC\n')
        self.assertEqual(self.m1.name, 'xx')

    def test_regular_to_model(self):
        """Regular seq should work with dense alignment"""
        a = ArrayAlignment([self.r1, self.r2])
        self.assertEqual(str(a), '>x\nAAA\n>y\nCCC\n')
        a = ArrayAlignment([self.r1, self.r2], moltype=DNA)
        self.assertEqual(str(a), '>x\nAAA\n>y\nCCC\n')
        self.assertEqual(self.r1.name, 'x')

    def test_model_to_regular(self):
        """Model seq should work with regular alignment"""
        a = Alignment([self.m1, self.m2])
        self.assertEqual(str(a), '>xx\nAAA\n>yy\nCCC\n')
        a = Alignment([self.m1, self.m2], moltype=DNA)
        self.assertEqual(str(a), '>xx\nAAA\n>yy\nCCC\n')
        self.assertEqual(self.m1.name, 'xx')

    def test_regular_to_regular(self):
        """Regular seq should work with regular alignment"""
        a = Alignment([self.r1, self.r2])
        self.assertEqual(str(a), '>x\nAAA\n>y\nCCC\n')
        a = Alignment([self.r1, self.r2], moltype=DNA)
        self.assertEqual(str(a), '>x\nAAA\n>y\nCCC\n')
        self.assertEqual(self.r1.name, 'x')

    def test_model_aln_to_regular_aln(self):
        """Dense aln should convert to regular aln"""
        a = ArrayAlignment([self.r1, self.r2])
        d = Alignment(a)
        self.assertEqual(str(d), '>x\nAAA\n>y\nCCC\n')
        d = Alignment(a, moltype=DNA)
        self.assertEqual(str(d), '>x\nAAA\n>y\nCCC\n')
        self.assertEqual(self.r1.name, 'x')

    def test_regular_aln_to_model_aln(self):
        """Regular aln should convert to model aln"""
        a = Alignment([self.r1, self.r2])
        d = ArrayAlignment(a)
        self.assertEqual(str(d), '>x\nAAA\n>y\nCCC\n')
        d = ArrayAlignment(a, moltype=DNA)
        self.assertEqual(str(d), '>x\nAAA\n>y\nCCC\n')
        self.assertEqual(self.r1.name, 'x')

    def test_regular_aln_to_regular_aln(self):
        """Regular aln should convert to regular aln"""
        a = Alignment([self.r1, self.r2])
        d = Alignment(a)
        self.assertEqual(str(d), '>x\nAAA\n>y\nCCC\n')
        d = Alignment(a, moltype=DNA)
        self.assertEqual(str(d), '>x\nAAA\n>y\nCCC\n')
        self.assertEqual(self.r1.name, 'x')

    def test_model_aln_to_model_aln(self):
        """Model aln should convert to model aln"""
        a = Alignment([self.r1, self.r2])
        d = Alignment(a)
        self.assertEqual(str(d), '>x\nAAA\n>y\nCCC\n')
        d = Alignment(a, moltype=DNA)
        self.assertEqual(str(d), '>x\nAAA\n>y\nCCC\n')
        self.assertEqual(self.r1.name, 'x')


# run tests if invoked from command line
if __name__ == '__main__':
    main()
