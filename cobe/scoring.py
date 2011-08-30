# Copyright (C) 2011 Peter Teichman

import math


class Scorer:
    def __init__(self, reverse=False):
        self.reverse = reverse

    def end(self, reply):
        pass

    def finish(self, score):
        if self.reverse:
            score = 1.0 - score

        return score

    def normalize(self, score):
        # map high-valued scores into 0..1
        if score < 0:
            return score

        return 1.0 - 1.0 / (1.0 + score)

    def score(self, reply):
        return NotImplementedError


class ScorerGroup:
    def __init__(self):
        self.scorers = []

    def add_scorer(self, weight, scorer):
        self.scorers.append((weight, scorer))

    def end(self, reply):
        for scorer in self.scorers:
            scorer[1].end(reply)

    def score(self, reply):
        score = 0.

        for weight, scorer in self.scorers:
            score += weight * scorer.score(reply)

        return score


class CobeScorer(Scorer):
    """Classic Cobe scorer"""
    def __init__(self):
        Scorer.__init__(self)

        self.cache = {}

    def score(self, reply):
        info = 0.

        get_probability = reply.graph.get_edge_probability

        cache = self.cache
        for edge in reply.edges:
            try:
                p = cache[edge.edge_id]
            except KeyError:
                p = get_probability(edge)
                cache[edge.edge_id] = p

            info += -math.log(p, 2)

        # Approximate the number of cobe 1.2 contexts in this reply, so the
        # scorer will have similar results.

        # First, we have (graph.order - 1) extra edges on either end of the
        # reply, since cobe 2.0 learns from (_END_TOKEN, _END_TOKEN, ...).
        n_words = len(reply.edges) - (reply.graph.order - 1) * 2

        # Add back one word for each space between edges, since cobe 1.2
        # treated those as separate parts of a context.
        for edge in reply.edges:
            if edge.has_space:
                n_words += 1

        if n_words > 8:
            info /= math.sqrt(n_words - 1)
        elif n_words >= 16:
            info /= n_words

        return self.finish(self.normalize(info))

    def end(self, reply):
        self.cache = {}

class InformationScorer(Scorer):
    """Score based on the information of each edge in the graph"""
    def score(self, reply):
        info = 0.
        for edge in reply.edges:
            info += -math.log(edge.probability, 2)

        # return the average information per word
        info /= len(reply.edges)

        return self.finish(self.normalize(info))


class LengthScorer(Scorer):
    def score(self, reply):
        return self.finish(self.normalize(len(reply.edges)))