# Teknik Rapor

`report.pdf` projenin nihai teknik raporudur (Türkçe, gövde 12 sayfa ve kaynakça).

Kaynaktan yeniden derlemek için bu klasörde şu komutu çalıştırın:

```bash
latexmk -xelatex report.tex
```

Derleme XeLaTeX, TeX Gyre Termes yazı tipi ve Türkçe heceleme desenleri (`texlive-lang-european`) gerektirir. Şekiller `fig/` klasöründedir ve `results/figures/` altındaki çıktılardan alınmıştır.
