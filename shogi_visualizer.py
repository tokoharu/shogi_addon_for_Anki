# -*- mode: Python ; coding: utf-8 -*-
#
# Copyright © 2018 tokoharu
# Parts taken from from anki/latex.py
# Copyright: Damien Elmes <anki@ichi2.net>
#
# The style is from the AnkiDroid code, presumably
# Copyright (c) 2012 Kostas Spyropoulos <inigo.aldana@gmail.com>
#
# License: GNU AGPL, version 3 or later;
# http://www.gnu.org/copyleft/agpl.html

"""
Add-on for Anki 2 to show a shogi board.
"""
import re
from collections import namedtuple

from anki.cards import Card
from anki.hooks import addHook

BOARD_SIZE = 150
__version__ = '1.0.0'

FenData = namedtuple(
    'FenData',
    ['placement', 'active', 'mochi', 'count'])
fen_re = re.compile(r"\[sfen\](.+?)\[/sfen\]", re.DOTALL | re.IGNORECASE)

piece = dict(zip("kgsnlbrp", u"玉金銀桂香角飛歩"))
promote = dict(zip(u"銀桂香角飛歩", u"全圭杏馬龍と"))
"""
promote = dict([(u"銀", u"成銀"), (u"桂", u"成桂"), (u"香", u"成香"),\
                (u"角", u"馬"), (u"飛", u"龍"), (u"歩", u"と")] )
"""

fen_template = u"""

<figure class="shogi_diagram">
<table class="shogi_mochi_gote">{gotemochi}</table>
<table class="shogi_board">{rows}</table>
<table class="shogi_mochi_sente">{sentemochi}</table>
<figcaption>
<span class="fen_extra active">{act}, </span>
<span class="fen_extra count">手数 : {count},</span>
<span class="fen_extra comment"> {other}</span>
</figcaption>
</figure>
"""


def shogi_card_css(self):
    """Add the shogi style to the card style """
    return u"""<style scoped>


.shogi_board {
  border:1px solid #333;
  border-spacing:0;
}

.shogi_board td {
  background: #fff
  -webkit-box-shadow: inset 0 0 0 1px #fff;
  font-size: 160%;
  height: 1.43em;
  width: 1.3em;
  border:1px solid #333;
  border-spacing:0;

  padding-top: 0;
  padding-bottom: 0;
  vertical-align : bottom;
  text-align: center;
}
.rev { -webkit-transform: rotate(180deg);}

figure.shogi_diagram  {
  display: inline-table;
}
figure.shogi_diagram table{
  display: inline-block;
}
figure.shogi_diagram figcaption{
  display: table-caption;
  caption-side: bottom;
}
.num {
    font-size : 50%;
}
.shogi_mochi_gote  {
  background: #fff;
  border: solid 1px #000000;
  height: 11em;
  width : 1.6em;
  font-size: 160%;
  -webkit-transform: rotate(180deg);
  margin-right :0.5em;
}
.shogi_mochi_sente  {
  background: #fff;
  border: solid 1px #000000;
  height: 11em;
  width : 1.6em;
  font-size: 160%;
  margin-left :0.5em;
}

</style>""".replace("160%", str(BOARD_SIZE)+"%") + old_css(self)


def counted_spaces(match):
    u"""Replace numbers with spaces"""
    return ' ' * int(match.group(0))


def get_mochi(origin):
    sente_res = list()
    gote_res = list()
    if origin == "-":
        return sente_res, gote_res
    tmp = ""
    for c in origin:
        if c.isdigit():
            tmp += c
        else:
            if tmp == "":
                tmp = "1"
            tmp = tuple([c.lower(), int(tmp)])
            if c.islower():
                gote_res.append(tmp)
            else:
                sente_res.append(tmp)
            tmp = ""
    return sente_res, gote_res


def format_mochi(p, val):
    return u"<tr><td>" + p + u"<span class=\"num\">" \
           + str(val) + u"</span>" + u"</td></tr>"


def insert_table(fen_match):
    u"""
    Replace well formed FEN data with a shogi board diagram.

    This is the worker function that replaces the actual data.
    """
    revflag = [False] * 200
    promoteflag = [False] * 200
    itr = 0
    fen_str = fen_match.group(1)
    spacesplit = fen_str.split(" ")
    for c in fen_str:
        if c.isdigit():
            itr += int(c)
            continue
        if c.islower():
            revflag[itr] = True
        if c == "+":
            promoteflag[itr] = True
            continue
        if c == "/":
            continue
        itr += 1

    fen_text = u''

    for c in fen_str:
        if c.isalpha():
            c = c.lower()
            try:
                fen_text += piece[c]
            except KeyError:
                fen_text += c
        else:
            fen_text += c
    try:
        fen = FenData(*(fen_text.split()))
    except TypeError:
        return fen_match.group(0)
    rows = fen.placement.split('/')
    active = u'.'
    if fen.active == "b":
        active = u"先手番"
    else:
        active = u"後手番"
    trows = []
    itr = 0
    for r in rows:
        assert(itr % 9 == 0)
        r = re.sub('[1-9][0-9]?', counted_spaces, r)
        tr = u'<tr>'
        remain = ""
        for p in r:
            if p == "+":
                remain = "+"
                continue
            if remain == "+":
                p = promote[p]
            remain = ""

            head = u'<td class=\"def\"'
            if len(p) == 2:
                head += u" class=\"press\" "
            head += u">"
            p = head + u"{0}</td>".format(p)
            if revflag[itr] is True:
                p = p.replace(u"def", u"rev")
            tr += p
            itr += 1
        trows.append(tr + u'</tr>\n')

    sente_mochi, gote_mochi = get_mochi(spacesplit[2])
    sente_str = ""
    gote_str = ""

    for p, val in gote_mochi:
        gote_str += format_mochi(piece[p], val)
    for p, val in sente_mochi:
        sente_str += format_mochi(piece[p], val)

    return fen_template.format(
        gotemochi=gote_str, sentemochi=sente_str,
        rows=''.join(trows), act=active, count=fen.count, other="")


def kanji_num(c):
    hoge = dict(zip(u"一二三四五六七八九十", range(1, 11)))
    try:
        return hoge[c]
    except:
        return 0


def insert_kif_table(txt):
    origin = txt.group(1)
    # print(origin)
    line_re = re.compile(r"<div>[^<]*</div>")
    stripdiv_re = re.compile(r"<div>(.*?)</div>")
    origin = "<div>" + origin + "</div>"
    line_data = line_re.findall(origin)
    boardflag = 0
    boardstr = []
    sente_str = ""
    gote_str = ""

    revBoard = False
    for line in line_data:
        if line.find(u"手数＝") >= 0 and line.find(u"▲") >= 0:
            revBoard = True

    def get_mochi_kif(line):
        line += "end"
        ret = ""
        posa = line.find(u"：")
        posb = line.find(u"end")
        mochi_data = line[(posa+1):(posb)].split(u"　")
        for pdata in mochi_data:
            val = 0
            for c in pdata:
                val += kanji_num(c)
            if val == 0:
                val = 1
            ret += format_mochi(pdata[0], val)
        return ret
    for line in line_data:
        # print(line)
        try:
            line = stripdiv_re.match(line).group(1)
        except:
            continue
        if line.find(u"後手の持駒") >= 0:
            if line.find(u"なし") >= 0:
                continue
            gote_str += get_mochi_kif(line)

        if line.find(u"先手の持駒") >= 0:
            if line.find(u"なし") >= 0:
                continue
            sente_str += get_mochi_kif(line)

        if line.find(u"+-----") >= 0:
            boardflag += 1
            continue
        if boardflag == 1:
            line_str = ""
            inner = 0
            revflag = False
            for c in line:
                if c == "|":
                    inner += 1
                    continue
                if inner != 1:
                    continue
                if c == "v":
                    revflag = True
                elif not c == u" ":
                    if c == u"・":
                        c = " "
                    tmp = u"<td class=\"def\">" + c + u"</td>"
                    if revflag + revBoard == 1:
                        tmp = tmp.replace(u"def", u"rev")
                    revflag = False
                    line_str += tmp
            if revBoard is True:
                tmp_re = re.compile(r"<td[^<]*</td>")
                tmp = tmp_re.findall(line_str)
                tmp = tmp[::-1]
                line_str = "".join(tmp)
            boardstr.append("<tr>" + line_str + "</tr>")

    comment = ""
    if revBoard is True:
        comment += u"(先後反転)"
        sente_str, gote_str = gote_str, sente_str
        boardstr = boardstr[::-1]

    rows = ''.join(boardstr)

    return fen_template.format(
        gotemochi=gote_str, sentemochi=sente_str,
        rows=rows, act="", count="", other=comment)


def make_kif_table(txt, *args):
    kif_re = re.compile(r"\[kif\](.+?)\[/kif\]", re.DOTALL | re.IGNORECASE)
    return kif_re.sub(insert_kif_table, txt)


def make_fen_table(txt, *args):
    return fen_re.sub(insert_table, txt)

old_css = Card.css
Card.css = shogi_card_css
addHook("mungeQA", make_fen_table)
addHook("mungeQA", make_kif_table)
