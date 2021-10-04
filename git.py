#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  4 18:18:45 2021

@author: ejetzer
"""

from subprocess import run
from pathlib import Path

class Repository:
    
    def __init__(self, path: Path):
        self.path = path
    
    def init(self):
        run(['git', 'init'], cwd=self.path)
    
    def clone(self, other: str):
        run(['git', 'clone', other], cwd=self.path)
    
    def add(self, *args):
        run(['git', 'add'] + list(args), cwd=self.path)
    
    def rm(self, *args):
        run(['git', 'rm'] + list(args), cwd=self.path)
    
    def commit(self, msg: str, *args):
        run(['git', 'commit', '-m', msg] + list(args), cwd=self.path)
    
    def pull(self):
        run(['git', 'pull'], cwd=self.path)
    
    def push(self):
        run(['git', 'push'], cwd=self.path)
    
    def status(self):
        run(['git', 'status'], cwd=self.path)
    
    def log(self):
        run(['git', 'log'], cwd=self.path)
    
    def branch(self, b: str = ''):
        run(['git', 'branch', b], cwd=self.path)


if __name__ == '__main__':
    path = Path('~/Desktop/test').expanduser()
    assert path.exists()
    repo = Repository(path)
    repo.init()
    with (path / 'test.txt').open('a') as f:
        f.write('hahaha')
    repo.add('test.txt')
    repo.commit('Ajout d\'un test')
    repo.status()