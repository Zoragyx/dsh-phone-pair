#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final repair of MainActivity.java after the PowerShell cp936 corruption.

Deterministic: reverse the byte corruption, then replace the 72 damaged lines by number
with their true content. All Chinese text comes from the exact string pool of the last
good build (artifacts/dsh-phone-1.3.apk) or from unambiguous Java structure.

Writes UTF-8 without BOM, LF. Asserts no damage marker survives and quotes are balanced.
"""
import io
import re
import sys

sys.path.insert(0, r"C:\Users\Zora\Documents\deepseek-harness\default-workspace\dsh-phone-app\tools")
from repair_stage2 import reverse_corruption, SRC

OUT = r"C:\Users\Zora\AppData\Local\Temp\MainActivity.repaired.java"

FIXED = {
    158: '        col.addView(label("DSH 手机版", 25, FG, true), spaced(0, dp(6)));',
    162: '            hintText = "已收到配对链接 \u00b7 输入密码后自动完成配对";',
    164: '            hintText = "本机配对已清除 \u00b7 进入后请重新配对";',
    166: '            hintText = setup ? "首次使用 \u00b7 请为这台手机设置进入密码" : "输入密码后才能进入";',
    174: '                        ? "密码只保存在本机（PBKDF2 加密），忘记后可随时重设。"',
    175: '                        : "密码只保存在本机，请勿告诉他人。",',
    180: '        final EditText first = passwordField(setup ? "设置密码（至少 4 位）" : "密码");',
    183: '        final EditText second = setup ? passwordField("再输入一次") : null;',
    194: '        submit.setText(setup ? "设置并进入" : "进入");',
    207: '        settings.setText("设置 / 帮助");',
    225: '            status.setText("尝试次数过多，请 " + ((cool + 999) / 1000) + " 秒后再试");',
    232: '                status.setText("密码至少 4 位");',
    236: '                status.setText("两次输入的密码不一致");',
    241: '            status.setText("正在保存…");',
    248: '                    toast("密码已设置");',
    256: '            status.setText("请输入密码");',
    261: '        status.setText("正在校验…");',
    275: '                    status.setText("密码不正确");',
    278: '                        status.setText("密码不正确，请 " + ((wait + 999) / 1000) + " 秒后再试");',
    533: '            showLoading("正在完成配对…");',
    535: '            showLoading("正在加载界面…");',
    548: '        toast("配对失败：配对链接可能已过期，请在电脑上重新生成");',
    559: '            toast("配对成功");',
    572: '        showLoading("正在重新下载界面…");',
    604: '        loadingLabel = label("正在加载界面…", 14, MUTED, false);',
    607: '        TextView tip = label("首次打开需要下载约 10 MB 客户端，之后会走本机缓存。", 12, MUTED, false);',
    624: '        TextView sub = label("请确认电脑上的 DSH 正在运行、手机网络可用后重试。", 13, MUTED, false);',
    634: '            showLoading("正在重试…");',
    697: '            toast("已收到配对链接，输入密码后自动配对");',
    710: '        final EditText input = plainField("粘贴配对链接或配对码");',
    716: '                .setTitle("重新配对")',
    717: '                .setMessage("在电脑上打开 DSH \u2192「远程访问」面板，复制配对链接发到手机，粘贴到这里。")',
    719: '                .setPositiveButton("确定", null)',
    726: '                        input.setError("链接格式不对");',
    735: '                        toast("解锁后将自动完成配对");',
    775: '        TextView title = label("需要重新配对", 20, FG, true);',
    780: '                "本机的配对凭据已被清除（重置本机数据，或在电脑端撤销了设备）。\\n\\n"',
    781: '                        + "1. 在电脑上打开 DSH \u2192「远程访问」面板\\n"',
    782: '                        + "2. 复制配对链接，发送到这台手机\\n"',
    783: '                        + "3. 粘贴到下面，或直接用手机打开该链接",',
    788: '        pairField = plainField("粘贴配对链接或配对码");',
    792: '        pair.setText("开始配对");',
    800: '                pairField.setError("链接格式不对");',
    812: '        settings.setText("设置 / 帮助");',
    831: '        items.add("修改进入密码");',
    832: '        items.add("重新配对（粘贴配对链接）");',
    833: '        items.add("复位：清除密码和配对");',
    834: '        items.add("关于本应用");',
    849: '                promptPassword("请输入密码以确认", () -> reloadForcing());',
    852: '                promptPassword("请输入当前密码", () -> promptNewPassword());',
    859: '                        .setTitle("复位本机")',
    860: '                        .setMessage("将清除本机的密码、网页缓存和配对凭据。"',
    861: '                                + "复位后必须用电脑上的配对链接重新配对，才能继续使用。")',
    862: '                        .setPositiveButton("确定复位", (d, w) -> {',
    868: '                            toast("已复位：请重设密码，然后重新配对");',
    877: '                        .setMessage("DSH 手机版 1.4\\n\\n"',
    878: '                                + "远程地址：" + AppConfig.BASE_HOST + "\\n"',
    879: '                                + "本 App 只是一个带密码锁的壳：界面完全来自你自己的 DSH 服务，"',
    880: '                                + "密码只在手机本地校验。\\n\\n"',
    881: '                                + "配对凭据内置在安装包内（作为首次启动的引导）；"',
    882: '                                + "「复位」会作废它，需要重新配对。请勿把安装包转发给他人；"',
    883: '                                + "如需作废，可在电脑「远程访问」面板中撤销本设备。")',
    884: '                        .setPositiveButton("知道了", null)',
    902: '                .setPositiveButton("确定", null)',
    914: '                        input.setError("密码不正确");',
    924: '        final EditText b = passwordField("再输入一次");',
    931: '                .setTitle("修改进入密码")',
    939: '                a.setError("至少 4 位");',
    943: '                b.setError("两次输入不一致");',
    948: '            toast("密码已更新");',
    1005: '                .setTitle("DSH 手机版")',
    1006: '                .setItems(new String[]{"设置 / 帮助", "退出到桌面"}, (d, w) -> {',
}

MARKERS = "\ue000\ufffd"


def main():
    text = reverse_corruption(open(SRC, "rb").read()).replace("\r\n", "\n")
    lines = text.split("\n")
    damaged = [i for i, l in enumerate(lines, 1) if any(c in l for c in MARKERS)]
    print("damaged lines: %d" % len(damaged))
    missing = [n for n in damaged if n not in FIXED]
    extra = [n for n in FIXED if n not in damaged]
    if missing:
        print("!! no rule for lines: %s" % missing)
    if extra:
        print("!! rule for undamaged lines: %s" % extra)
    for n in damaged:
        if n in FIXED:
            lines[n - 1] = FIXED[n]

    text = "\n".join(lines)
    left = sum(text.count(c) for c in MARKERS)
    odd = [(i, l.strip()) for i, l in enumerate(text.split("\n"), 1) if l.count('"') % 2]
    print("markers left: %d ; lines with odd quote count: %d" % (left, len(odd)))
    for i, l in odd[:20]:
        print("   odd %d | %s" % (i, l))
    if left == 0 and not missing and not extra and not odd:
        data = text.encode("utf-8")
        open(OUT, "wb").write(data)
        print("wrote %s (%d bytes, no BOM, LF, %d lines)" % (OUT, len(data), len(lines)))
    else:
        print("NOT WRITTEN")


if __name__ == "__main__":
    main()
