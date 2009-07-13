# -*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand
from django.utils.translation import ugettext_noop as _
from languages.models import Language

class Command(NoArgsCommand):
    help = 'Create or Update the default languages.'

    requires_model_validation = False
    can_import_settings = True

    def handle_noargs(self, **options):
        print "Creating or updating languages"
        process_lang()
        print "Default set of languages initialized successfully."

def process_lang():
    """Create or Update the default languages"""

    #####################################################
    #    KEEP THE ORDERING BY LANGUAGE CODE

    # TODO: It is ugly and temporary, we need to find a good way to handle it.

    af, created = Language.objects.get_or_create(code='af')
    af.name = _(u'Afrikaans')
    af.specialchars = u'ëïêôûáéíóúý'
    af.nplurals = '2'
    af.pluralequation = '(n != 1)'
    af.save()

#  Akan
#   ak.name = _(u'Akan')
#   ak.pluralequation = u'(n > 1)'
#   ak.specialchars = 'ɛɔƐƆ'
#   ak.nplurals = u'2'

#   Amharic
    am, created = Language.objects.get_or_create(code='am')
    am.name = _(u'Amharic')
    am.save()

#   Arabic
    ar, created = Language.objects.get_or_create(code='ar')
    ar.name = _(u'Arabic')
    ar.nplurals = '6'
    ar.pluralequation = 'n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 && n%100<=99 ? 4 : 5'
    ar.save()

#   Argentinian Spanish
    es_ar, created = Language.objects.get_or_create(code='es_AR')
    es_ar.name = _(u'Spanish (Argentinian)')
    es_ar.nplurals = '2'
    es_ar.pluralequation = '(n != 1)'
    es_ar.save()

#   Assamese
    as_, created = Language.objects.get_or_create(code='as')
    as_.name = _(u'Assamese')
    as_.nplurals = '2'
    as_.pluralequation = '(n!=1)'
    as_.save()

#   Asturian
    ast, created = Language.objects.get_or_create(code='ast')
    ast.name = _(u'Asturian')
    ast.nplurals = '2'
    ast.pluralequation = '(n!=1)'
    ast.save()

#   Azərbaycan
#   Azerbaijani
    az, created = Language.objects.get_or_create(code='az')
    az.name = _(u'Azerbaijani')
    az.nplurals = '2'
    az.pluralequation = '(n != 1)'
    az.save()

#   Balochi (bal)
    bal, created = Language.objects.get_or_create(code='bal')
    bal.name = _(u'Balochi')
    bal.save()

#   Беларуская
#   Belarusian
    be, created = Language.objects.get_or_create(code='be')
    be.name = _(u'Belarusian')
    be.nplurals = '3'
    be.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    be.save()

#   Български
#   Bulgarian
    bg, created = Language.objects.get_or_create(code='bg')
    bg.name = _(u'Bulgarian')
    bg.nplurals = '2'
    bg.pluralequation = '(n != 1)'
    bg.save()

#   বাংলা
#   Bengali
    bn, created = Language.objects.get_or_create(code='bn')
    bn.name = _(u'Bengali')
    bn.nplurals = '2'
    bn.pluralequation = '(n != 1)'
    bn.save()

#   Bengali (India)
    bn_IN, created = Language.objects.get_or_create(code='bn_IN')
    bn_IN.code_aliases='bn-in bn-IN'
    bn_IN.name = _(u'Bengali (India)')
    bn_IN.nplurals = '2'
    bn_IN.pluralequation = '(n != 1)'
    bn_IN.save()

#   Tibetan
#   bo.name = _(u'Tibetan')
#   bo.nplurals = '1'
#   bo.pluralequation = '0'

#   Bosanski
#   Bosnian
    bs, created = Language.objects.get_or_create(code='bs')
    bs.name = _(u'Bosnian')
    bs.nplurals = '3'
    bs.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    bs.save()

#   Català
#   Catalan
    ca, created = Language.objects.get_or_create(code='ca')
    ca.name = _(u'Catalan (Valencian)')
    ca.nplurals = '2'
    ca.pluralequation = '(n != 1)'
    ca.save()

#   Česky
#   Czech
    cs, created = Language.objects.get_or_create(code='cs')
    cs.name = _(u'Czech')
    cs.nplurals = '3'
    cs.pluralequation = '(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2'
    cs.save()

#   Cymraeg
#   Welsh
    cy, created = Language.objects.get_or_create(code='cy')
    cy.name = _(u'Welsh')
    cy.nplurals = '2'
    cy.pluralequation = '(n==2) ? 1 : 0'
    cy.save()

#   Dansk
#   Danish
    da, created = Language.objects.get_or_create(code='da')
    da.name = _(u'Danish')
    da.nplurals = '2'
    da.pluralequation = '(n != 1)'
    da.save()

#   Deutsch
#   German
    de, created = Language.objects.get_or_create(code='de')
    de.name = _(u'German')
    de.nplurals = '2'
    de.pluralequation = '(n != 1)'
    de.save()

#   Swiss German
    de_CH, created = Language.objects.get_or_create(code='de_CH')
    de_CH.code_aliases='de-ch de-CH'
    de_CH.name = _(u'Swiss German')
    de_CH.nplurals = '2'
    de_CH.pluralequation = '(n != 1)'
    de_CH.save()

#   ང་ཁ
#   Dzongkha
    dz, created = Language.objects.get_or_create(code='dz')
    dz.name = _(u'Dzongkha')
    dz.nplurals = '1'
    dz.pluralequation = '0'
    dz.save()

#   Ελληνικά
#   Greek
    el, created = Language.objects.get_or_create(code='el')
    el.name = _(u'Greek')
    el.nplurals = '2'
    el.pluralequation = '(n != 1)'
    el.save()

#   English
    en, created = Language.objects.get_or_create(code='en')
    en.name = _(u'English')
    en.nplurals = '2'
    en.pluralequation = '(n != 1)'
    en.save()

#   English (United Kingdom)
    en_GB, created = Language.objects.get_or_create(code='en_GB')
    en_GB.code_aliases = 'en-gb en-GB'
    en_GB.name = _(u'English (United Kingdom)')
    en_GB.nplurals = '2'
    en_GB.pluralequation = '(n != 1)'
    en_GB.save()

#   English (South Africa)
    en_ZA, created = Language.objects.get_or_create(code='en_ZA')
    en_ZA.code_aliases = 'en-za en-ZA'
    en_ZA.name = _(u'English (South Africa)')
    en_ZA.nplurals = '2'
    en_ZA.pluralequation = '(n != 1)'
    en_ZA.save()

#   Esperanto
#   eo.name = _(u'Esperanto')
#   eo.nplurals = '2'
#   eo.pluralequation = '(n != 1)'

#   Español
#   Spanish
    es, created = Language.objects.get_or_create(code='es')
    es.name = _(u'Spanish (Castilian)')
    es.nplurals = '2'
    es.pluralequation = '(n != 1)'
    es.save()

#   Eesti
#   Estonian
    et, created = Language.objects.get_or_create(code='et')
    et.name = _(u'Estonian')
    et.nplurals = '2'
    et.pluralequation = '(n != 1)'
    et.save()

#   Euskara
#   Basque
    eu, created = Language.objects.get_or_create(code='eu')
    eu.name = _(u'Basque')
    eu.nplurals = '2'
    eu.pluralequation = '(n != 1)'
    eu.save()

#   Persian
    fa, created = Language.objects.get_or_create(code='fa')
    fa.name = _(u'Persian')
    fa.nplurals = '1'
    fa.pluralequation = '0'
    fa.save()

#   Suomi
#   Finnish
    fi, created = Language.objects.get_or_create(code='fi')
    fi.name = _(u'Finnish')
    fi.nplurals = '2'
    fi.pluralequation = '(n != 1)'
    fi.save()

#   Føroyskt
#   Faroese
#   fo.name = _(u'Faroese')
#   fo.nplurals = '2'
#   fo.pluralequation = '(n != 1)'

#   Français
#   French
    fr, created = Language.objects.get_or_create(code='fr')
    fr.name = _(u'French')
    fr.nplurals = '2'
    fr.pluralequation = '(n > 1)'
    fr.save()

#   Furlan
#   Friulian
    fur, created = Language.objects.get_or_create(code='fur')
    fur.name = _(u'Friulian')
    fur.nplurals = '2'
    fur.pluralequation = '(n != 1)'
    fur.save()

#   Frysk
#   Frisian
    fy, created = Language.objects.get_or_create(code='fy')
    fy.name = _(u'Western Frisian')
    fy.nplurals = '2'
    fy.pluralequation = '(n != 1)'
    fy.save()

#   Gaeilge
#   Irish
    ga, created = Language.objects.get_or_create(code='ga')
    ga.name = _(u'Irish')
    ga.nplurals = '3'
    ga.pluralequation = 'n==1 ? 0 : n==2 ? 1 : 2'
    ga.save()

#   Galego
#   Galician
    gl, created = Language.objects.get_or_create(code='gl')
    gl.name = _(u'Galician')
    gl.nplurals = '2'
    gl.pluralequation = '(n != 1)'
    gl.save()

#   ગુજરાતી
#   Gujarati
    gu, created = Language.objects.get_or_create(code='gu')
    gu.name = _(u'Gujarati')
    gu.nplurals = '2'
    gu.pluralequation = '(n != 1)'
    gu.save()

#   Hebrew
    he, created = Language.objects.get_or_create(code='he')
    he.name = _(u'Hebrew')
    he.nplurals = '2'
    he.pluralequation = '(n != 1)'
    he.save()

#   हिन्दी
#   Hindi
    hi, created = Language.objects.get_or_create(code='hi')
    hi.name = _(u'Hindi')
    hi.nplurals = '2'
    hi.pluralequation = '(n != 1)'
    hi.save()

#   Hrvatski
#   Croatian
    hr, created = Language.objects.get_or_create(code='hr')
    hr.name = _(u'Croatian')
    hr.nplurals = '3'
    hr.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    hr.save()

#   Haitian Creole
    ht, created = Language.objects.get_or_create(code='ht')
    ht.name = _(u'Haitian (Haitian Creole)')
    ht.nplurals = '2'
    ht.pluralequation = '(n !=1)'
    ht.save()

#   Magyar
#   Hungarian
    hu, created = Language.objects.get_or_create(code='hu')
    hu.name = _(u'Hungarian')
    hu.nplurals = '2'
    hu.pluralequation = '(n !=1)'
    hu.save()

#   Armenian
    hy, created = Language.objects.get_or_create(code='hy')
    hy.name = _('Armenian')
    hy.save()

#   Bahasa Indonesia
#   Indonesian
    id, created = Language.objects.get_or_create(code='id')
    id.name = _(u'Indonesian')
    id.nplurals = '1'
    id.pluralequation = '0'
    id.save()

#   Iloko
    ilo, created = Language.objects.get_or_create(code='ilo')
    ilo.name = _('Iloko') 
    ilo.save()

#   Icelandic
    islang, created = Language.objects.get_or_create(code='is')
    islang.name = _(u'Icelandic')
    islang.nplurals = '2'
    islang.pluralequation = '(n != 1)'
    islang.save()

#   Italiano
#   Italian
    it, created = Language.objects.get_or_create(code='it')
    it.name = _(u'Italian')
    it.nplurals = '2'
    it.pluralequation = '(n != 1)'
    it.save()

#   日本語
#   Japanese
    ja, created = Language.objects.get_or_create(code='ja')
    ja.name = _(u'Japanese')
    ja.nplurals = '1'
    ja.pluralequation = '0'
    ja.save()

#   ქართული
#   Georgian
    ka, created = Language.objects.get_or_create(code='ka')
    ka.name = _(u'Georgian')
    ka.nplurals = '1'
    ka.pluralequation = '0'
    ka.save()

#   ភាសា
#   Khmer
#   km.name = _(u'Khmer')
#   km.nplurals = '1'
#   km.pluralequation = '0'

#   Kannada
    kn, created = Language.objects.get_or_create(code='kn')
    kn.name = _('Kannada')
    kn.save() 

#   한국어
#   Korean
    ko, created = Language.objects.get_or_create(code='ko')
    ko.name = _(u'Korean')
    ko.nplurals = '1'
    ko.pluralequation = '0'
    ko.save()

#   Kashmiri
    ks, created = Language.objects.get_or_create(code='ks')
    ks.name = _(u'Kashmiri')
    ks.nplurals = '2'
    ks.pluralequation = '(n != 1)'
    ks.save()

#   Kurdî / كوردي
#   Kurdish
    ku, created = Language.objects.get_or_create(code='ku')
    ku.name = _(u'Kurdish')
    ku.nplurals = '2'
    ku.pluralequation = '(n != 1)'
    ku.save()

#   Lëtzebuergesch
#   Letzeburgesch
#   lb.name = _(u'Letzeburgesch')
#   lb.nplurals = '2'
#   lb.pluralequation = '(n != 1)'

#   Lao
    lo, created = Language.objects.get_or_create(code='lo')
    lo.name = _('Lao')
    lo.save()

#   Lietuvių
#   Lithuanian
    lt, created = Language.objects.get_or_create(code='lt')
    lt.name = _(u'Lithuanian')
    lt.nplurals = '3'
    lt.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && (n%100<10 || n%100>=20) ? 1 : 2)'
    lt.save()

#   Latviešu
#   Latvian
    lv, created = Language.objects.get_or_create(code='lv')
    lv.name = _(u'Latvian')
    lv.nplurals = '3'
    lv.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n != 0 ? 1 : 2)'
    lv.save()

#   Maithili
    mai, created = Language.objects.get_or_create(code='mai')
    mai.name = _('Maithili')
    mai.save()

#   Macedonian
    mk, created = Language.objects.get_or_create(code='mk')
    mk.name = _('Macedonian')
    mk.save()

#   Malayalam
    ml, created = Language.objects.get_or_create(code='ml')
    ml.name = _(u'Malayalam')
    ml.nplurals = '2'
    ml.pluralequation = '(n != 1)'
    ml.save()

#   Malagasy
#   mg.name = _(u'Malagasy')
#   mg.nplurals = '2'
#   mg.pluralequation = '(n > 1)'

#   Монгол
#   Mongolian
    mn, created = Language.objects.get_or_create(code='mn')
    mn.name = _(u'Mongolian')
    mn.nplurals = '2'
    mn.pluralequation = '(n != 1)'
    mn.save()

#   Marathi
    mr, created = Language.objects.get_or_create(code='mr')
    mr.name = _(u'Marathi')
    mr.nplurals = u'2'
    mr.pluralequation = u'(n != 1)'
    mr.save()

#   Malay
    ms, created = Language.objects.get_or_create(code='ms')
    ms.name = _(u'Malay')
    ms.nplurals = u'1'
    ms.pluralequation = u'0'
    ms.save()

#   Malti
#   Maltese
    mt, created = Language.objects.get_or_create(code='mt')
    mt.name = _(u'Maltese')
    mt.nplurals = '4'
    mt.pluralequation = '(n==1 ? 0 : n==0 || ( n%100>1 && n%100<11) ? 1 : (n%100>10 && n%100<20 ) ? 2 : 3)'
    mt.save()

#   Burmese
    my, created = Language.objects.get_or_create(code='my')
    my.name = _('Burmese')
    my.save()

#   Nahuatl
#   nah.name = _(u'Nahuatl')
#   nah.nplurals = '2'
#   nah.pluralequation = '(n != 1)'

#   Bokmål
#   Norwegian Bokmål
    nb, created = Language.objects.get_or_create(code='nb')
    nb.name = _('Norwegian Bokmål')
    nb.nplurals = '2'
    nb.pluralequation = '(n != 1)'
    nb.save()

#   Nepali\
    ne, created = Language.objects.get_or_create(code='ne')
    ne.name = _(u'Nepali')
    ne.nplurals = u'2'
    ne.pluralequation = u'(n != 1)'
    ne.save()

#   Nederlands
#   Dutch
    nl, created = Language.objects.get_or_create(code='nl')
    nl.name = _(u'Dutch (Flemish)')
    nl.nplurals = '2'
    nl.pluralequation = '(n != 1)'
    nl.save()

#   Nynorsk
#   Norwegian Nynorsk
    nn, created = Language.objects.get_or_create(code='nn')
    nn.name = _(u'Norwegian Nynorsk')
    nn.nplurals = '2'
    nn.pluralequation = '(n != 1)'
    nn.save()

#   Norwegian
    no, created = Language.objects.get_or_create(code='no')
    no.name = _('Norwegian')
    no.save()

#   Sesotho sa Leboa
#   Northern Sotho
    nso, created = Language.objects.get_or_create(code='nso')
    nso.name = _(u'Northern Sotho')
    nso.nplurals = '2'
    nso.pluralequation = '(n > 1)'
    nso.specialchars = 'šŠ'
    nso.save()

#   Oriya
    or_, created = Language.objects.get_or_create(code='or')
    or_.name = _(u'Oriya')
    or_.nplurals = '2'
    or_.pluralequation = '(n != 1)'
    or_.save()
    
#   Punjabi
    pa, created = Language.objects.get_or_create(code='pa')
    pa.name = _(u'Panjabi (Punjabi)')
    pa.nplurals = '2'
    pa.pluralequation = '(n != 1)'
    pa.save()
    
#   Papiamento
#   pap.name = _(u'Papiamento')
#   pap.nplurals = '2'
#   pap.pluralequation = '(n != 1)'

#   Polski
#   Polish
    pl, created = Language.objects.get_or_create(code='pl')
    pl.name = _(u'Polish')
    pl.nplurals = '3'
    pl.pluralequation = '(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    pl.save()

#   Pashto
#   FIXME the plurals don't seem right but that is what is out in the field
#   ps, created = Language.objects.get_or_create(code='ps')
#   ps.name = _(u'Pushto (Pashto)')
#   ps.nplurals = '2'
#   ps.pluralequation = '(n != 1)'
#   ps.save()

#   Português
#   Portuguese
    pt, created = Language.objects.get_or_create(code='pt')
    pt.name = _(u'Portuguese')
    pt.nplurals = '2'
    pt.pluralequation = '(n != 1)'
    pt.save()

#   Português do Brasil
#   Brazilian Portuguese
    pt_BR, created = Language.objects.get_or_create(code='pt_BR')
    pt_BR.code_aliases = 'pt-br pt-BR'
    pt_BR.name = _(u'Brazilian Portuguese')
    pt_BR.nplurals = '2'
    pt_BR.pluralequation = '(n > 1)'
    pt_BR.save()

#   Română
#   Romanian
    ro, created = Language.objects.get_or_create(code='ro')
    ro.name = _(u'Romanian')
    ro.nplurals = '3'
    ro.pluralequation = '(n==1 ? 0 : (n==0 || (n%100 > 0 && n%100 < 20)) ? 1 : 2);'
    ro.save()

#   Русский
#   Russian
    ru, created = Language.objects.get_or_create(code='ru')
    ru.name = _(u'Russian')
    ru.nplurals = '3'
    ru.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    ru.save()

#   Sinhala
    si, created = Language.objects.get_or_create(code='si')
    si.name = _('Sinhala')
    si.save()

#   Slovenčina
#   Slovak
    sk, created = Language.objects.get_or_create(code='sk')
    sk.name = _(u'Slovak')
    sk.nplurals = '3'
    sk.pluralequation = '(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2'
    sk.save()

#   Slovenščina
#   Slovenian
    sl, created = Language.objects.get_or_create(code='sl')
    sl.name = _(u'Slovenian')
    sl.nplurals = '4'
    sl.pluralequation = '(n%100==1 ? 0 : n%100==2 ? 1 : n%100==3 || n%100==4 ? 2 : 3)'
    sl.save()

#   Shqip
#   Albanian
    sq, created = Language.objects.get_or_create(code='sq')
    sq.name = _(u'Albanian')
    sq.nplurals = '2'
    sq.pluralequation = '(n != 1)'
    sq.save()

#   Српски / Srpski
#   Serbian
    sr, created = Language.objects.get_or_create(code='sr')
    sr.name = _(u'Serbian')
    sr.nplurals = '3'
    sr.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    sr.save()

#   Serbian
    srLatin, created = Language.objects.get_or_create(code='sr@latin')
    srLatin.code_aliases = 'sr@Latin sr@latn sr@Latn'
    srLatin.name = _(u'Serbian (Latin)')
    srLatin.nplurals = '3'
    srLatin.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    srLatin.save()


#   Sesotho
#   Sotho
    st, created = Language.objects.get_or_create(code='st')
    st.name = _(u'Sotho, Southern')
    st.nplurals = '2'
    st.pluralequation = '(n != 1)'
    st.save()

#   Svenska
#   Swedish
    sv, created = Language.objects.get_or_create(code='sv')
    sv.name = _(u'Swedish')
    sv.nplurals = '2'
    sv.pluralequation = '(n != 1)'
    sv.save()

#   தமிழ்
#   Tamil
    ta, created = Language.objects.get_or_create(code='ta')
    ta.name = _(u'Tamil')
    ta.nplurals = '2'
    ta.pluralequation = '(n != 1)'
    ta.save()

#   Telugu
    te, created = Language.objects.get_or_create(code='te')
    te.name = _('Telugu')
    te.save()

#   Tajik
    tg, created = Language.objects.get_or_create(code='tg')
    tg.name = _('Tajik')
    tg.save()

#   Thai
    th, created = Language.objects.get_or_create(code='th')
    th.name = _('Thai')
    th.save()

#   Tagalog
    tl, created = Language.objects.get_or_create(code='tl')
    tl.name = _('Tagalog')
    tl.save()

#   Туркмен / تركمن
#   Turkmen
#   tk.name = _(u'Turkmen')
#   tk.nplurals = '2'
#   tk.pluralequation = '(n != 1)'

#   Türkçe
#   Turkish
    tr, created = Language.objects.get_or_create(code='tr')
    tr.name = _(u'Turkish')
    tr.nplurals = '1'
    tr.pluralequation = '0'
    tr.save()

#   Urdu
    ur, created = Language.objects.get_or_create(code='ur')
    ur.name = _('Urdu')
    ur.save()

#   Українська
#   Ukrainian
    uk, created = Language.objects.get_or_create(code='uk')
    uk.name = _(u'Ukrainian')
    uk.nplurals = '3'
    uk.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    uk.save()

#   Tshivenḓa
#   Venda
#   ve.name = _(u'Venda')
#   ve.nplurals = '2'
#   ve.pluralequation = '(n != 1)'
#   ve.specialchars = 'ḓṋḽṱ ḒṊḼṰ ṅṄ'

#   Vietnamese
    vi, created = Language.objects.get_or_create(code='vi')
    vi.name = _(u'Vietnamese')
    vi.nplurals = '1'
    vi.pluralequation = '0'
    vi.save()

#   Wolof
    wo, created = Language.objects.get_or_create(code='wo')
    wo.name = _(u'Wolof')
    wo.nplurals = '2'
    wo.pluralequation = '(n != 1)'
    wo.save()

#   Walon
#   Walloon
#   wa.name = _(u'Waloon')
#   wa.nplurals = '2'
#   wa.pluralequation = '(n > 1)'

#   简体中文
#   Simplified Chinese (China mainland used below, but also used in Singapore and Malaysia)
    zh_CN, created = Language.objects.get_or_create(code='zh_CN')
    zh_CN.code_aliases = 'zh-cn zh-CN'
    zh_CN.name = _(u'Chinese (China)')
    zh_CN.nplurals = '1'
    zh_CN.pluralequation = '0'
    zh_CN.specialchars = u'←→↔×÷©…—‘’“”【】《》'
    zh_CN.save()

#   繁體中文
#   Traditional Chinese (Hong Kong used below, but also used in Taiwan and Macau)
    zh_HK, created = Language.objects.get_or_create(code='zh_HK')
    zh_HK.code_aliases = 'zh-hk zh-HK'
    zh_HK.name = _(u'Chinese (Hong Kong)')
    zh_HK.nplurals = '1'
    zh_HK.pluralequation = '0'
    zh_HK.specialchars = u'←→↔×÷©…—‘’“”「」『』【】《》'
    zh_HK.save()

#   繁體中文
#   Traditional Chinese (Taiwan used below, but also used in Hong Kong and Macau)
    zh_TW, created = Language.objects.get_or_create(code='zh_TW')
    zh_TW.code_aliases = 'zh-tw zh-TW'
    zh_TW.name = _(u'Chinese (Taiwan)')
    zh_TW.nplurals = '1'
    zh_TW.pluralequation = '0'
    zh_TW.specialchars = u'←→↔×÷©…—‘’“”「」『』【】《》'
    zh_TW.save()

#   Zulu
    zu, created = Language.objects.get_or_create(code='zu')
    zu.name = _('Zulu')
    zu.save()
