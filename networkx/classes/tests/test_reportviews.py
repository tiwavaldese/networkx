from nose.tools import assert_equal, assert_not_equal, \
    assert_true, assert_false, assert_raises, \
    assert_is, assert_is_not

import networkx as nx


# Nodes
class TestNodeView(object):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9)
        cls.nv = cls.G.nodes   # NodeView(G)

    def test_pickle(self):
        import pickle
        nv = self.nv
        pnv = pickle.loads(pickle.dumps(nv, -1))
        assert_equal(nv, pnv)
        assert_equal(nv.__slots__, pnv.__slots__)

    def test_str(self):
        assert_equal(str(self.nv), "[0, 1, 2, 3, 4, 5, 6, 7, 8]")

    def test_repr(self):
        assert_equal(repr(self.nv), "NodeView((0, 1, 2, 3, 4, 5, 6, 7, 8))")

    def test_contains(self):
        nv = self.nv
        assert_true(7 in nv)
        assert_false(9 in nv)
        self.G.remove_node(7)
        self.G.add_node(9)
        assert_false(7 in nv)
        assert_true(9 in nv)

    def test_getitem(self):
        nv = self.nv
        self.G.nodes[3]['foo'] = 'bar'
        assert_equal(nv[7], {})
        assert_equal(nv[3], {'foo': 'bar'})

    def test_iter(self):
        nv = self.nv
        for i, n in enumerate(nv):
            assert_equal(i, n)
        inv = iter(nv)
        assert_equal(next(inv), 0)
        assert_not_equal(iter(nv), nv)
        assert_equal(iter(inv), inv)
        inv2 = iter(nv)
        next(inv2)
        assert_equal(list(inv), list(inv2))
        # odd case where NodeView calls NodeDataView with data=False
        nnv = nv(data=False)
        for i, n in enumerate(nnv):
            assert_equal(i, n)

    def test_call(self):
        nodes = self.nv
        assert_is(nodes, nodes())
        assert_is_not(nodes, nodes(data=True))
        assert_is_not(nodes, nodes(data='weight'))


class TestNodeDataView(object):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9)
        cls.nv = cls.G.nodes.data()   # NodeDataView(G)
        cls.ndv = cls.G.nodes.data(True)
        cls.nwv = cls.G.nodes.data('foo')

    def test_viewtype(self):
        nv = self.G.nodes
        ndvfalse = nv.data(False)
        assert_is(nv, ndvfalse)
        assert_is_not(nv, self.ndv)

    def test_pickle(self):
        import pickle
        nv = self.nv
        pnv = pickle.loads(pickle.dumps(nv, -1))
        assert_equal(nv, pnv)
        assert_equal(nv.__slots__, pnv.__slots__)

    def test_str(self):
        msg = str([(n, {}) for n in range(9)])
        assert_equal(str(self.ndv), msg)

    def test_repr(self):
        msg = "NodeDataView({0: {}, 1: {}, 2: {}, 3: {}, " + \
              "4: {}, 5: {}, 6: {}, 7: {}, 8: {}})"
        assert_equal(repr(self.ndv), msg)

    def test_contains(self):
        self.G.nodes[3]['foo'] = 'bar'
        assert_true((7, {}) in self.nv)
        assert_true((3, {'foo': 'bar'}) in self.nv)
        assert_true((3, 'bar') in self.nwv)
        assert_true((7, None) in self.nwv)
        # default
        nwv_def = self.G.nodes(data='foo', default='biz')
        assert_true((7, 'biz') in nwv_def)
        assert_true((3, 'bar') in nwv_def)

    def test_getitem(self):
        self.G.nodes[3]['foo'] = 'bar'
        assert_equal(self.nv[3], {'foo': 'bar'})
        # default
        nwv_def = self.G.nodes(data='foo', default='biz')
        assert_true(nwv_def[7], 'biz')
        assert_equal(nwv_def[3], 'bar')

    def test_iter(self):
        nv = self.nv
        for i, (n, d) in enumerate(nv):
            assert_equal(i, n)
            assert_equal(d, {})
        inv = iter(nv)
        assert_equal(next(inv), (0, {}))
        self.G.nodes[3]['foo'] = 'bar'
        # default
        for n, d in nv:
            if n == 3:
                assert_equal(d, {'foo': 'bar'})
            else:
                assert_equal(d, {})
        # data=True
        for n, d in self.ndv:
            if n == 3:
                assert_equal(d, {'foo': 'bar'})
            else:
                assert_equal(d, {})
        # data='foo'
        for n, d in self.nwv:
            if n == 3:
                assert_equal(d, 'bar')
            else:
                assert_equal(d, None)
        # data='foo', default=1
        for n, d in self.G.nodes.data('foo', default=1):
            if n == 3:
                assert_equal(d, 'bar')
            else:
                assert_equal(d, 1)


def test_nodedataview_unhashable():
    G = nx.path_graph(9)
    G.nodes[3]['foo'] = 'bar'
    nvs = [G.nodes.data()]
    nvs.append(G.nodes.data(True))
    H = G.copy()
    H.nodes[4]['foo'] = {1, 2, 3}
    nvs.append(H.nodes.data(True))
    # raise unhashable
    for nv in nvs:
        assert_raises(TypeError, set, nv)
        assert_raises(TypeError, eval, 'nv | nv', locals())
    # no raise... hashable
    Gn = G.nodes.data(False)
    set(Gn)
    Gn | Gn
    Gn = G.nodes.data('foo')
    set(Gn)
    Gn | Gn


class TestNodeViewSetOps(object):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9)
        cls.G.nodes[3]['foo'] = 'bar'
        cls.nv = cls.G.nodes

    def n_its(self, nodes):
        return {node for node in nodes}

    def test_len(self):
        nv = self.nv
        assert_equal(len(nv), 9)
        self.G.remove_node(7)
        assert_equal(len(nv), 8)
        self.G.add_node(9)
        assert_equal(len(nv), 9)

    def test_and(self):
        # print("G & H nodes:", gnv & hnv)
        nv = self.nv
        some_nodes = self.n_its(range(5, 12))
        assert_equal(nv & some_nodes, self.n_its(range(5, 9)))
        assert_equal(some_nodes & nv, self.n_its(range(5, 9)))

    def test_or(self):
        # print("G | H nodes:", gnv | hnv)
        nv = self.nv
        some_nodes = self.n_its(range(5, 12))
        assert_equal(nv | some_nodes, self.n_its(range(12)))
        assert_equal(some_nodes | nv, self.n_its(range(12)))

    def test_xor(self):
        # print("G ^ H nodes:", gnv ^ hnv)
        nv = self.nv
        some_nodes = self.n_its(range(5, 12))
        nodes = {0, 1, 2, 3, 4, 9, 10, 11}
        assert_equal(nv ^ some_nodes, self.n_its(nodes))
        assert_equal(some_nodes ^ nv, self.n_its(nodes))

    def test_sub(self):
        # print("G - H nodes:", gnv - hnv)
        nv = self.nv
        some_nodes = self.n_its(range(5, 12))
        assert_equal(nv - some_nodes, self.n_its(range(5)))
        assert_equal(some_nodes - nv, self.n_its(range(9, 12)))


class TestNodeDataViewSetOps(TestNodeViewSetOps):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9)
        cls.G.nodes[3]['foo'] = 'bar'
        cls.nv = cls.G.nodes.data('foo')

    def n_its(self, nodes):
        return {(node, 'bar' if node == 3 else None) for node in nodes}


class TestNodeDataViewDefaultSetOps(TestNodeDataViewSetOps):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9)
        cls.G.nodes[3]['foo'] = 'bar'
        cls.nv = cls.G.nodes.data('foo', default=1)

    def n_its(self, nodes):
        return {(node, 'bar' if node == 3 else 1) for node in nodes}


# Edges Data View
class TestEdgeDataView(object):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9)
        cls.eview = nx.reportviews.EdgeView

    def test_pickle(self):
        import pickle
        ev = self.eview(self.G)(data=True)
        pev = pickle.loads(pickle.dumps(ev, -1))
        assert_equal(list(ev), list(pev))
        assert_equal(ev.__slots__, pev.__slots__)

    def modify_edge(self, G, e, **kwds):
        self.G._adj[e[0]][e[1]].update(kwds)

    def test_str(self):
        ev = self.eview(self.G)(data=True)
        rep = str([(n, n + 1, {}) for n in range(8)])
        assert_equal(str(ev), rep)

    def test_repr(self):
        ev = self.eview(self.G)(data=True)
        rep = "EdgeDataView([(0, 1, {}), (1, 2, {}), " + \
              "(2, 3, {}), (3, 4, {}), " + \
              "(4, 5, {}), (5, 6, {}), " + \
              "(6, 7, {}), (7, 8, {})])"
        assert_equal(repr(ev), rep)

    def test_iterdata(self):
        G = self.G
        evr = self.eview(G)
        ev = evr(data=True)
        ev_def = evr(data='foo', default=1)

        for u, v, d in ev:
            pass
        assert_equal(d, {})

        for u, v, wt in ev_def:
            pass
        assert_equal(wt, 1)

        self.modify_edge(G, (2, 3), foo='bar')
        for e in ev:
            assert_equal(len(e), 3)
            if set(e[:2]) == {2, 3}:
                assert_equal(e[2], {'foo': 'bar'})
                checked = True
            else:
                assert_equal(e[2], {})
        assert_true(checked)

        for e in ev_def:
            assert_equal(len(e), 3)
            if set(e[:2]) == {2, 3}:
                assert_equal(e[2], 'bar')
                checked_wt = True
            else:
                assert_equal(e[2], 1)
        assert_true(checked_wt)

    def test_iter(self):
        evr = self.eview(self.G)
        ev = evr()
        for u, v in ev:
            pass
        iev = iter(ev)
        assert_equal(next(iev), (0, 1))
        assert_not_equal(iter(ev), ev)
        assert_equal(iter(iev), iev)

    def test_contains(self):
        evr = self.eview(self.G)
        ev = evr()
        if self.G.is_directed():
            assert_true((1, 2) in ev and (2, 1) not in ev)
        else:
            assert_true((1, 2) in ev and (2, 1) in ev)
        assert_false((1, 4) in ev)
        assert_false((1, 90) in ev)
        assert_false((90, 1) in ev)

    def test_len(self):
        evr = self.eview(self.G)
        ev = evr(data='foo')
        assert_equal(len(ev), 8)
        assert_equal(len(evr(1)), 2)
        assert_equal(len(evr([1, 2, 3])), 4)

        assert_equal(len(self.G.edges(1)), 2)
        assert_equal(len(self.G.edges()), 8)
        assert_equal(len(self.G.edges), 8)

        H = self.G.copy()
        H.add_edge(1, 1)
        assert_equal(len(H.edges(1)), 3)
        assert_equal(len(H.edges()), 9)
        assert_equal(len(H.edges), 9)


class TestOutEdgeDataView(TestEdgeDataView):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9, create_using=nx.DiGraph())
        cls.eview = nx.reportviews.OutEdgeView

    def test_repr(self):
        ev = self.eview(self.G)(data=True)
        rep = "OutEdgeDataView([(0, 1, {}), (1, 2, {}), " + \
              "(2, 3, {}), (3, 4, {}), " + \
              "(4, 5, {}), (5, 6, {}), " + \
              "(6, 7, {}), (7, 8, {})])"
        assert_equal(repr(ev), rep)

    def test_len(self):
        evr = self.eview(self.G)
        ev = evr(data='foo')
        assert_equal(len(ev), 8)
        assert_equal(len(evr(1)), 1)
        assert_equal(len(evr([1, 2, 3])), 3)

        assert_equal(len(self.G.edges(1)), 1)
        assert_equal(len(self.G.edges()), 8)
        assert_equal(len(self.G.edges), 8)

        H = self.G.copy()
        H.add_edge(1, 1)
        assert_equal(len(H.edges(1)), 2)
        assert_equal(len(H.edges()), 9)
        assert_equal(len(H.edges), 9)


class TestInEdgeDataView(TestOutEdgeDataView):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9, create_using=nx.DiGraph())
        cls.eview = nx.reportviews.InEdgeView

    def test_repr(self):
        ev = self.eview(self.G)(data=True)
        rep = "InEdgeDataView([(0, 1, {}), (1, 2, {}), " + \
              "(2, 3, {}), (3, 4, {}), " + \
              "(4, 5, {}), (5, 6, {}), " + \
              "(6, 7, {}), (7, 8, {})])"
        assert_equal(repr(ev), rep)


class TestMultiEdgeDataView(TestEdgeDataView):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9, create_using=nx.MultiGraph())
        cls.eview = nx.reportviews.MultiEdgeView

    def modify_edge(self, G, e, **kwds):
        self.G._adj[e[0]][e[1]][0].update(kwds)

    def test_repr(self):
        ev = self.eview(self.G)(data=True)
        rep = "MultiEdgeDataView([(0, 1, {}), (1, 2, {}), " + \
              "(2, 3, {}), (3, 4, {}), " + \
              "(4, 5, {}), (5, 6, {}), " + \
              "(6, 7, {}), (7, 8, {})])"
        assert_equal(repr(ev), rep)


class TestOutMultiEdgeDataView(TestOutEdgeDataView):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9, create_using=nx.MultiDiGraph())
        cls.eview = nx.reportviews.OutMultiEdgeView

    def modify_edge(self, G, e, **kwds):
        self.G._adj[e[0]][e[1]][0].update(kwds)

    def test_repr(self):
        ev = self.eview(self.G)(data=True)
        rep = "OutMultiEdgeDataView([(0, 1, {}), (1, 2, {}), " + \
              "(2, 3, {}), (3, 4, {}), " + \
              "(4, 5, {}), (5, 6, {}), " + \
              "(6, 7, {}), (7, 8, {})])"
        assert_equal(repr(ev), rep)


class TestInMultiEdgeDataView(TestOutMultiEdgeDataView):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9, create_using=nx.MultiDiGraph())
        cls.eview = nx.reportviews.InMultiEdgeView

    def test_repr(self):
        ev = self.eview(self.G)(data=True)
        rep = "InMultiEdgeDataView([(0, 1, {}), (1, 2, {}), " + \
              "(2, 3, {}), (3, 4, {}), " + \
              "(4, 5, {}), (5, 6, {}), " + \
              "(6, 7, {}), (7, 8, {})])"
        assert_equal(repr(ev), rep)


# Edge Views
class TestEdgeView(object):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9)
        cls.eview = nx.reportviews.EdgeView

    def test_pickle(self):
        import pickle
        ev = self.eview(self.G)
        pev = pickle.loads(pickle.dumps(ev, -1))
        assert_equal(ev, pev)
        assert_equal(ev.__slots__, pev.__slots__)

    def modify_edge(self, G, e, **kwds):
        self.G._adj[e[0]][e[1]].update(kwds)

    def test_str(self):
        ev = self.eview(self.G)
        rep = str([(n, n + 1) for n in range(8)])
        assert_equal(str(ev), rep)

    def test_repr(self):
        ev = self.eview(self.G)
        rep = "EdgeView([(0, 1), (1, 2), (2, 3), (3, 4), " + \
            "(4, 5), (5, 6), (6, 7), (7, 8)])"
        assert_equal(repr(ev), rep)

    def test_call(self):
        ev = self.eview(self.G)
        assert_equal(id(ev), id(ev()))
        assert_equal(id(ev), id(ev(data=False)))
        assert_not_equal(id(ev), id(ev(data=True)))
        assert_not_equal(id(ev), id(ev(nbunch=1)))

    def test_data(self):
        ev = self.eview(self.G)
        assert_not_equal(id(ev), id(ev.data()))
        assert_equal(id(ev), id(ev.data(data=False)))
        assert_not_equal(id(ev), id(ev.data(data=True)))
        assert_not_equal(id(ev), id(ev.data(nbunch=1)))

    def test_iter(self):
        ev = self.eview(self.G)
        for u, v in ev:
            pass
        iev = iter(ev)
        assert_equal(next(iev), (0, 1))
        assert_not_equal(iter(ev), ev)
        assert_equal(iter(iev), iev)

    def test_contains(self):
        ev = self.eview(self.G)
        edv = ev()
        if self.G.is_directed():
            assert_true((1, 2) in ev and (2, 1) not in ev)
            assert_true((1, 2) in edv and (2, 1) not in edv)
        else:
            assert_true((1, 2) in ev and (2, 1) in ev)
            assert_true((1, 2) in edv and (2, 1) in edv)
        assert_false((1, 4) in ev)
        assert_false((1, 4) in edv)
        # edge not in graph
        assert_false((1, 90) in ev)
        assert_false((90, 1) in ev)
        assert_false((1, 90) in edv)
        assert_false((90, 1) in edv)

    def test_len(self):
        ev = self.eview(self.G)
        num_ed = 9 if self.G.is_multigraph() else 8
        assert_equal(len(ev), num_ed)

        H = self.G.copy()
        H.add_edge(1, 1)
        assert_equal(len(H.edges(1)), 3 + H.is_multigraph() - H.is_directed())
        assert_equal(len(H.edges()), num_ed + 1)
        assert_equal(len(H.edges), num_ed + 1)

    def test_and(self):
        # print("G & H edges:", gnv & hnv)
        ev = self.eview(self.G)
        some_edges = {(0, 1), (1, 0), (0, 2)}
        if self.G.is_directed():
            assert_true(some_edges & ev, {(0, 1)})
            assert_true(ev & some_edges, {(0, 1)})
        else:
            assert_equal(ev & some_edges, {(0, 1), (1, 0)})
            assert_equal(some_edges & ev, {(0, 1), (1, 0)})
        return

    def test_or(self):
        # print("G | H edges:", gnv | hnv)
        ev = self.eview(self.G)
        some_edges = {(0, 1), (1, 0), (0, 2)}
        result1 = {(n, n + 1) for n in range(8)}
        result1.update(some_edges)
        result2 = {(n + 1, n) for n in range(8)}
        result2.update(some_edges)
        assert_true((ev | some_edges) in (result1, result2))
        assert_true((some_edges | ev) in (result1, result2))

    def test_xor(self):
        # print("G ^ H edges:", gnv ^ hnv)
        ev = self.eview(self.G)
        some_edges = {(0, 1), (1, 0), (0, 2)}
        if self.G.is_directed():
            result = {(n, n + 1) for n in range(1, 8)}
            result.update({(1, 0), (0, 2)})
            assert_equal(ev ^ some_edges, result)
        else:
            result = {(n, n + 1) for n in range(1, 8)}
            result.update({(0, 2)})
            assert_equal(ev ^ some_edges, result)
        return

    def test_sub(self):
        # print("G - H edges:", gnv - hnv)
        ev = self.eview(self.G)
        some_edges = {(0, 1), (1, 0), (0, 2)}
        result = {(n, n + 1) for n in range(8)}
        result.remove((0, 1))
        assert_true(ev - some_edges, result)


class TestOutEdgeView(TestEdgeView):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9, nx.DiGraph())
        cls.eview = nx.reportviews.OutEdgeView

    def test_repr(self):
        ev = self.eview(self.G)
        rep = "OutEdgeView([(0, 1), (1, 2), (2, 3), (3, 4), " + \
            "(4, 5), (5, 6), (6, 7), (7, 8)])"
        assert_equal(repr(ev), rep)


class TestInEdgeView(TestEdgeView):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9, nx.DiGraph())
        cls.eview = nx.reportviews.InEdgeView

    def test_repr(self):
        ev = self.eview(self.G)
        rep = "InEdgeView([(0, 1), (1, 2), (2, 3), (3, 4), " + \
            "(4, 5), (5, 6), (6, 7), (7, 8)])"
        assert_equal(repr(ev), rep)


class TestMultiEdgeView(TestEdgeView):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9, nx.MultiGraph())
        cls.G.add_edge(1, 2, key=3, foo='bar')
        cls.eview = nx.reportviews.MultiEdgeView

    def modify_edge(self, G, e, **kwds):
        if len(e) == 2:
            e = e + (0,)
        self.G._adj[e[0]][e[1]][e[2]].update(kwds)

    def test_str(self):
        ev = self.eview(self.G)
        replist = [(n, n + 1, 0) for n in range(8)]
        replist.insert(2, (1, 2, 3))
        rep = str(replist)
        assert_equal(str(ev), rep)

    def test_repr(self):
        ev = self.eview(self.G)
        rep = "MultiEdgeView([(0, 1, 0), (1, 2, 0), (1, 2, 3), (2, 3, 0), " + \
            "(3, 4, 0), (4, 5, 0), (5, 6, 0), (6, 7, 0), (7, 8, 0)])"
        assert_equal(repr(ev), rep)

    def test_call(self):
        ev = self.eview(self.G)
        assert_equal(id(ev), id(ev(keys=True)))
        assert_equal(id(ev), id(ev(data=False, keys=True)))
        assert_not_equal(id(ev), id(ev(keys=False)))
        assert_not_equal(id(ev), id(ev(data=True)))
        assert_not_equal(id(ev), id(ev(nbunch=1)))

    def test_data(self):
        ev = self.eview(self.G)
        assert_not_equal(id(ev), id(ev.data()))
        assert_equal(id(ev), id(ev.data(data=False, keys=True)))
        assert_not_equal(id(ev), id(ev.data(keys=False)))
        assert_not_equal(id(ev), id(ev.data(data=True)))
        assert_not_equal(id(ev), id(ev.data(nbunch=1)))

    def test_iter(self):
        ev = self.eview(self.G)
        for u, v, k in ev:
            pass
        iev = iter(ev)
        assert_equal(next(iev), (0, 1, 0))
        assert_not_equal(iter(ev), ev)
        assert_equal(iter(iev), iev)

    def test_iterkeys(self):
        G = self.G
        evr = self.eview(G)
        ev = evr(keys=True)
        for u, v, k in ev:
            pass
        assert_equal(k, 0)
        ev = evr(keys=True, data="foo", default=1)
        for u, v, k, wt in ev:
            pass
        assert_equal(wt, 1)

        self.modify_edge(G, (2, 3, 0), foo='bar')
        ev = evr(keys=True, data=True)
        for e in ev:
            assert_equal(len(e), 4)
            print('edge:', e)
            if set(e[:2]) == {2, 3}:
                print(self.G._adj[2][3])
                assert_equal(e[2], 0)
                assert_equal(e[3], {'foo': 'bar'})
                checked = True
            elif set(e[:3]) == {1, 2, 3}:
                assert_equal(e[2], 3)
                assert_equal(e[3], {'foo': 'bar'})
                checked_multi = True
            else:
                assert_equal(e[2], 0)
                assert_equal(e[3], {})
        assert_true(checked)
        assert_true(checked_multi)
        ev = evr(keys=True, data='foo', default=1)
        for e in ev:
            if set(e[:2]) == {1, 2} and e[2] == 3:
                assert_equal(e[3], 'bar')
            if set(e[:2]) == {1, 2} and e[2] == 0:
                assert_equal(e[3], 1)
            if set(e[:2]) == {2, 3}:
                assert_equal(e[2], 0)
                assert_equal(e[3], 'bar')
                assert_equal(len(e), 4)
                checked_wt = True
        assert_true(checked_wt)
        ev = evr(keys=True)
        for e in ev:
            assert_equal(len(e), 3)
        elist = sorted([(i, i + 1, 0) for i in range(8)] + [(1, 2, 3)])
        assert_equal(sorted(list(ev)), elist)
        # test order of arguments:graph, nbunch, data, keys, default
        ev = evr((1, 2), 'foo', True, 1)
        for e in ev:
            if set(e[:2]) == {1, 2}:
                assert_true(e[2] in {0, 3})
                if e[2] == 3:
                    assert_equal(e[3], 'bar')
                else:  # e[2] == 0
                    assert_equal(e[3], 1)
        if G.is_directed():
            assert_equal(len(list(ev)), 3)
        else:
            assert_equal(len(list(ev)), 4)

    def test_or(self):
        # print("G | H edges:", gnv | hnv)
        ev = self.eview(self.G)
        some_edges = {(0, 1, 0), (1, 0, 0), (0, 2, 0)}
        result = {(n, n + 1, 0) for n in range(8)}
        result.update(some_edges)
        result.update({(1, 2, 3)})
        assert_equal(ev | some_edges, result)
        assert_equal(some_edges | ev, result)

    def test_sub(self):
        # print("G - H edges:", gnv - hnv)
        ev = self.eview(self.G)
        some_edges = {(0, 1, 0), (1, 0, 0), (0, 2, 0)}
        result = {(n, n + 1, 0) for n in range(8)}
        result.remove((0, 1, 0))
        result.update({(1, 2, 3)})
        assert_true(ev - some_edges, result)
        assert_true(some_edges - ev, result)

    def test_xor(self):
        # print("G ^ H edges:", gnv ^ hnv)
        ev = self.eview(self.G)
        some_edges = {(0, 1, 0), (1, 0, 0), (0, 2, 0)}
        if self.G.is_directed():
            result = {(n, n + 1, 0) for n in range(1, 8)}
            result.update({(1, 0, 0), (0, 2, 0), (1, 2, 3)})
            assert_equal(ev ^ some_edges, result)
            assert_equal(some_edges ^ ev, result)
        else:
            result = {(n, n + 1, 0) for n in range(1, 8)}
            result.update({(0, 2, 0), (1, 2, 3)})
            assert_equal(ev ^ some_edges, result)
            assert_equal(some_edges ^ ev, result)

    def test_and(self):
        # print("G & H edges:", gnv & hnv)
        ev = self.eview(self.G)
        some_edges = {(0, 1, 0), (1, 0, 0), (0, 2, 0)}
        if self.G.is_directed():
            assert_equal(ev & some_edges, {(0, 1, 0)})
            assert_equal(some_edges & ev, {(0, 1, 0)})
        else:
            assert_equal(ev & some_edges, {(0, 1, 0), (1, 0, 0)})
            assert_equal(some_edges & ev, {(0, 1, 0), (1, 0, 0)})


class TestOutMultiEdgeView(TestMultiEdgeView):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9, nx.MultiDiGraph())
        cls.G.add_edge(1, 2, key=3, foo='bar')
        cls.eview = nx.reportviews.OutMultiEdgeView

    def modify_edge(self, G, e, **kwds):
        if len(e) == 2:
            e = e + (0,)
        self.G._adj[e[0]][e[1]][e[2]].update(kwds)

    def test_repr(self):
        ev = self.eview(self.G)
        rep = "OutMultiEdgeView([(0, 1, 0), (1, 2, 0), (1, 2, 3), (2, 3, 0),"\
              + " (3, 4, 0), (4, 5, 0), (5, 6, 0), (6, 7, 0), (7, 8, 0)])"
        assert_equal(repr(ev), rep)


class TestInMultiEdgeView(TestMultiEdgeView):
    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(9, nx.MultiDiGraph())
        cls.G.add_edge(1, 2, key=3, foo='bar')
        cls.eview = nx.reportviews.InMultiEdgeView

    def modify_edge(self, G, e, **kwds):
        if len(e) == 2:
            e = e + (0,)
        self.G._adj[e[0]][e[1]][e[2]].update(kwds)

    def test_repr(self):
        ev = self.eview(self.G)
        rep = "InMultiEdgeView([(0, 1, 0), (1, 2, 0), (1, 2, 3), (2, 3, 0), "\
              + "(3, 4, 0), (4, 5, 0), (5, 6, 0), (6, 7, 0), (7, 8, 0)])"
        assert_equal(repr(ev), rep)


# Degrees
class TestDegreeView(object):
    GRAPH = nx.Graph
    dview = nx.reportviews.DegreeView

    @classmethod
    def setup_class(cls):
        cls.G = nx.path_graph(6, cls.GRAPH())
        cls.G.add_edge(1, 3, foo=2)
        cls.G.add_edge(1, 3, foo=3)

    def test_pickle(self):
        import pickle
        deg = self.G.degree
        pdeg = pickle.loads(pickle.dumps(deg, -1))
        assert_equal(dict(deg), dict(pdeg))

    def test_str(self):
        dv = self.dview(self.G)
        rep = str([(0, 1), (1, 3), (2, 2), (3, 3), (4, 2), (5, 1)])
        assert_equal(str(dv), rep)
        dv = self.G.degree()
        assert_equal(str(dv), rep)

    def test_repr(self):
        dv = self.dview(self.G)
        rep = "DegreeView({0: 1, 1: 3, 2: 2, 3: 3, 4: 2, 5: 1})"
        assert_equal(repr(dv), rep)

    def test_iter(self):
        dv = self.dview(self.G)
        for n, d in dv:
            pass
        idv = iter(dv)
        assert_not_equal(iter(dv), dv)
        assert_equal(iter(idv), idv)
        assert_equal(next(idv), (0, dv[0]))
        assert_equal(next(idv), (1, dv[1]))
        # weighted
        dv = self.dview(self.G, weight='foo')
        for n, d in dv:
            pass
        idv = iter(dv)
        assert_not_equal(iter(dv), dv)
        assert_equal(iter(idv), idv)
        assert_equal(next(idv), (0, dv[0]))
        assert_equal(next(idv), (1, dv[1]))

    def test_nbunch(self):
        dv = self.dview(self.G)
        dvn = dv(0)
        assert_equal(dvn, 1)
        dvn = dv([2, 3])
        assert_equal(sorted(dvn), [(2, 2), (3, 3)])

    def test_getitem(self):
        dv = self.dview(self.G)
        assert_equal(dv[0], 1)
        assert_equal(dv[1], 3)
        assert_equal(dv[2], 2)
        assert_equal(dv[3], 3)
        dv = self.dview(self.G, weight='foo')
        assert_equal(dv[0], 1)
        assert_equal(dv[1], 5)
        assert_equal(dv[2], 2)
        assert_equal(dv[3], 5)

    def test_weight(self):
        dv = self.dview(self.G)
        dvw = dv(0, weight='foo')
        assert_equal(dvw, 1)
        dvw = dv(1, weight='foo')
        assert_equal(dvw, 5)
        dvw = dv([2, 3], weight='foo')
        assert_equal(sorted(dvw), [(2, 2), (3, 5)])
        dvd = dict(dv(weight='foo'))
        assert_equal(dvd[0], 1)
        assert_equal(dvd[1], 5)
        assert_equal(dvd[2], 2)
        assert_equal(dvd[3], 5)

    def test_len(self):
        dv = self.dview(self.G)
        assert_equal(len(dv), 6)


class TestDiDegreeView(TestDegreeView):
    GRAPH = nx.DiGraph
    dview = nx.reportviews.DiDegreeView

    def test_repr(self):
        dv = self.G.degree()
        rep = "DiDegreeView({0: 1, 1: 3, 2: 2, 3: 3, 4: 2, 5: 1})"
        assert_equal(repr(dv), rep)


class TestOutDegreeView(TestDegreeView):
    GRAPH = nx.DiGraph
    dview = nx.reportviews.OutDegreeView

    def test_str(self):
        dv = self.dview(self.G)
        rep = str([(0, 1), (1, 2), (2, 1), (3, 1), (4, 1), (5, 0)])
        assert_equal(str(dv), rep)
        dv = self.G.out_degree()
        assert_equal(str(dv), rep)

    def test_repr(self):
        dv = self.G.out_degree()
        rep = "OutDegreeView({0: 1, 1: 2, 2: 1, 3: 1, 4: 1, 5: 0})"
        assert_equal(repr(dv), rep)

    def test_nbunch(self):
        dv = self.dview(self.G)
        dvn = dv(0)
        assert_equal(dvn, 1)
        dvn = dv([2, 3])
        assert_equal(sorted(dvn), [(2, 1), (3, 1)])

    def test_getitem(self):
        dv = self.dview(self.G)
        assert_equal(dv[0], 1)
        assert_equal(dv[1], 2)
        assert_equal(dv[2], 1)
        assert_equal(dv[3], 1)
        dv = self.dview(self.G, weight='foo')
        assert_equal(dv[0], 1)
        assert_equal(dv[1], 4)
        assert_equal(dv[2], 1)
        assert_equal(dv[3], 1)

    def test_weight(self):
        dv = self.dview(self.G)
        dvw = dv(0, weight='foo')
        assert_equal(dvw, 1)
        dvw = dv(1, weight='foo')
        assert_equal(dvw, 4)
        dvw = dv([2, 3], weight='foo')
        assert_equal(sorted(dvw), [(2, 1), (3, 1)])
        dvd = dict(dv(weight='foo'))
        assert_equal(dvd[0], 1)
        assert_equal(dvd[1], 4)
        assert_equal(dvd[2], 1)
        assert_equal(dvd[3], 1)


class TestInDegreeView(TestDegreeView):
    GRAPH = nx.DiGraph
    dview = nx.reportviews.InDegreeView

    def test_str(self):
        dv = self.dview(self.G)
        rep = str([(0, 0), (1, 1), (2, 1), (3, 2), (4, 1), (5, 1)])
        assert_equal(str(dv), rep)
        dv = self.G.in_degree()
        assert_equal(str(dv), rep)

    def test_repr(self):
        dv = self.G.in_degree()
        rep = "InDegreeView({0: 0, 1: 1, 2: 1, 3: 2, 4: 1, 5: 1})"
        assert_equal(repr(dv), rep)

    def test_nbunch(self):
        dv = self.dview(self.G)
        dvn = dv(0)
        assert_equal(dvn, 0)
        dvn = dv([2, 3])
        assert_equal(sorted(dvn), [(2, 1), (3, 2)])

    def test_getitem(self):
        dv = self.dview(self.G)
        assert_equal(dv[0], 0)
        assert_equal(dv[1], 1)
        assert_equal(dv[2], 1)
        assert_equal(dv[3], 2)
        dv = self.dview(self.G, weight='foo')
        assert_equal(dv[0], 0)
        assert_equal(dv[1], 1)
        assert_equal(dv[2], 1)
        assert_equal(dv[3], 4)

    def test_weight(self):
        dv = self.dview(self.G)
        dvw = dv(0, weight='foo')
        assert_equal(dvw, 0)
        dvw = dv(1, weight='foo')
        assert_equal(dvw, 1)
        dvw = dv([2, 3], weight='foo')
        assert_equal(sorted(dvw), [(2, 1), (3, 4)])
        dvd = dict(dv(weight='foo'))
        assert_equal(dvd[0], 0)
        assert_equal(dvd[1], 1)
        assert_equal(dvd[2], 1)
        assert_equal(dvd[3], 4)


class TestMultiDegreeView(TestDegreeView):
    GRAPH = nx.MultiGraph
    dview = nx.reportviews.MultiDegreeView

    def test_str(self):
        dv = self.dview(self.G)
        rep = str([(0, 1), (1, 4), (2, 2), (3, 4), (4, 2), (5, 1)])
        assert_equal(str(dv), rep)
        dv = self.G.degree()
        assert_equal(str(dv), rep)

    def test_repr(self):
        dv = self.G.degree()
        rep = "MultiDegreeView({0: 1, 1: 4, 2: 2, 3: 4, 4: 2, 5: 1})"
        assert_equal(repr(dv), rep)

    def test_nbunch(self):
        dv = self.dview(self.G)
        dvn = dv(0)
        assert_equal(dvn, 1)
        dvn = dv([2, 3])
        assert_equal(sorted(dvn), [(2, 2), (3, 4)])

    def test_getitem(self):
        dv = self.dview(self.G)
        assert_equal(dv[0], 1)
        assert_equal(dv[1], 4)
        assert_equal(dv[2], 2)
        assert_equal(dv[3], 4)
        dv = self.dview(self.G, weight='foo')
        assert_equal(dv[0], 1)
        assert_equal(dv[1], 7)
        assert_equal(dv[2], 2)
        assert_equal(dv[3], 7)

    def test_weight(self):
        dv = self.dview(self.G)
        dvw = dv(0, weight='foo')
        assert_equal(dvw, 1)
        dvw = dv(1, weight='foo')
        assert_equal(dvw, 7)
        dvw = dv([2, 3], weight='foo')
        assert_equal(sorted(dvw), [(2, 2), (3, 7)])
        dvd = dict(dv(weight='foo'))
        assert_equal(dvd[0], 1)
        assert_equal(dvd[1], 7)
        assert_equal(dvd[2], 2)
        assert_equal(dvd[3], 7)


class TestDiMultiDegreeView(TestMultiDegreeView):
    GRAPH = nx.MultiDiGraph
    dview = nx.reportviews.DiMultiDegreeView

    def test_repr(self):
        dv = self.G.degree()
        rep = "DiMultiDegreeView({0: 1, 1: 4, 2: 2, 3: 4, 4: 2, 5: 1})"
        assert_equal(repr(dv), rep)


class TestOutMultiDegreeView(TestDegreeView):
    GRAPH = nx.MultiDiGraph
    dview = nx.reportviews.OutMultiDegreeView

    def test_str(self):
        dv = self.dview(self.G)
        rep = str([(0, 1), (1, 3), (2, 1), (3, 1), (4, 1), (5, 0)])
        assert_equal(str(dv), rep)
        dv = self.G.out_degree()
        assert_equal(str(dv), rep)

    def test_repr(self):
        dv = self.G.out_degree()
        rep = "OutMultiDegreeView({0: 1, 1: 3, 2: 1, 3: 1, 4: 1, 5: 0})"
        assert_equal(repr(dv), rep)

    def test_nbunch(self):
        dv = self.dview(self.G)
        dvn = dv(0)
        assert_equal(dvn, 1)
        dvn = dv([2, 3])
        assert_equal(sorted(dvn), [(2, 1), (3, 1)])

    def test_getitem(self):
        dv = self.dview(self.G)
        assert_equal(dv[0], 1)
        assert_equal(dv[1], 3)
        assert_equal(dv[2], 1)
        assert_equal(dv[3], 1)
        dv = self.dview(self.G, weight='foo')
        assert_equal(dv[0], 1)
        assert_equal(dv[1], 6)
        assert_equal(dv[2], 1)
        assert_equal(dv[3], 1)

    def test_weight(self):
        dv = self.dview(self.G)
        dvw = dv(0, weight='foo')
        assert_equal(dvw, 1)
        dvw = dv(1, weight='foo')
        assert_equal(dvw, 6)
        dvw = dv([2, 3], weight='foo')
        assert_equal(sorted(dvw), [(2, 1), (3, 1)])
        dvd = dict(dv(weight='foo'))
        assert_equal(dvd[0], 1)
        assert_equal(dvd[1], 6)
        assert_equal(dvd[2], 1)
        assert_equal(dvd[3], 1)


class TestInMultiDegreeView(TestDegreeView):
    GRAPH = nx.MultiDiGraph
    dview = nx.reportviews.InMultiDegreeView

    def test_str(self):
        dv = self.dview(self.G)
        rep = str([(0, 0), (1, 1), (2, 1), (3, 3), (4, 1), (5, 1)])
        assert_equal(str(dv), rep)
        dv = self.G.in_degree()
        assert_equal(str(dv), rep)

    def test_repr(self):
        dv = self.G.in_degree()
        rep = "InMultiDegreeView({0: 0, 1: 1, 2: 1, 3: 3, 4: 1, 5: 1})"
        assert_equal(repr(dv), rep)

    def test_nbunch(self):
        dv = self.dview(self.G)
        dvn = dv(0)
        assert_equal(dvn, 0)
        dvn = dv([2, 3])
        assert_equal(sorted(dvn), [(2, 1), (3, 3)])

    def test_getitem(self):
        dv = self.dview(self.G)
        assert_equal(dv[0], 0)
        assert_equal(dv[1], 1)
        assert_equal(dv[2], 1)
        assert_equal(dv[3], 3)
        dv = self.dview(self.G, weight='foo')
        assert_equal(dv[0], 0)
        assert_equal(dv[1], 1)
        assert_equal(dv[2], 1)
        assert_equal(dv[3], 6)

    def test_weight(self):
        dv = self.dview(self.G)
        dvw = dv(0, weight='foo')
        assert_equal(dvw, 0)
        dvw = dv(1, weight='foo')
        assert_equal(dvw, 1)
        dvw = dv([2, 3], weight='foo')
        assert_equal(sorted(dvw), [(2, 1), (3, 6)])
        dvd = dict(dv(weight='foo'))
        assert_equal(dvd[0], 0)
        assert_equal(dvd[1], 1)
        assert_equal(dvd[2], 1)
        assert_equal(dvd[3], 6)
