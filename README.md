You can run `python portmanteau.py` in your terminal and access the web app on the designated port.

# Welcome to the portmanteau generator!

## About the Project

### What is a portmanteau?

Even if you've never mashed two words together yourself, it's likely that you've been making use of portmanteaus your whole life. Portmanteaus are formed by taking two or more words and blending their sounds together in order to create a new word that combines their meanings. Popular English portmanteaus include "motel" (motor + hotel), "brunch" (breakfast + lunch), "mockumentary" (mock + documentary), and "smog" (smoke + fog).

Linguistically speaking, portmanteaus (also referred to as blends), can becategorized in several different ways. For the pruposes of this project, we've decided to focus on continuous phonologically overlapping portmanteaus, meaning that we're looking to generate portmanteaus based on the longest set of sounds that are shared between the two input words. However, not every word has sounds in common with every other word, so depending on the words you input, you may end up with a non-overlapping portmanteau, which we've computed by joining the first word up to its middlemost vowel with the second word after its first vowel. In rare cases , we'll generate a reverse portmanteau, where the word you enter second is chosen to be the first word, in order to avoid some of the weirder sounding and looking combinations that can result.

### Acknowledgements

This tool makes use of the [Carnegie Mellon Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict).

## About the Team

### Leora Baumgarten, Backend

Leora has come up with some pretty good portmantueas over the years, but there are at least three (or maybe three hundred) groan-worthy blends for every clever one she shares—just ask her friends and family. She designed this project so that she could impress everyone with its masterful portmanteaus. She's currently working towards an M.S. in computational linguistics at Brandeis University, where she gets to explore her passion for language and language technology.

### Kayla Lin, Frontend

Kayla is not as good as portmanteaus as Leora, and cannot impress friends and family with portmanteaus. She is currently working on a B.A, studying Computer Science at the University of Rochester. She also enjoys a little CSS here and there.
