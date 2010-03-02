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
    af.code_aliases='af-ZA'
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
    am.code_aliases='am-ET'
    am.name = _(u'Amharic')
    am.save()

#   Arabic
    ar, created = Language.objects.get_or_create(code='ar')
    ar.code_aliases='ar-SA'
    ar.name = _(u'Arabic')
    ar.nplurals = '6'
    ar.pluralequation = 'n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 && n%100<=99 ? 4 : 5'
    ar.save()

#   Assamese
    as_, created = Language.objects.get_or_create(code='as')
    as_.code_aliases='as-IN'
    as_.name = _(u'Assamese')
    as_.nplurals = '2'
    as_.pluralequation = '(n!=1)'
    as_.save()

#   Asturian
    ast, created = Language.objects.get_or_create(code='ast')
    ast.code_aliases='ast-ES'
    ast.name = _(u'Asturian')
    ast.nplurals = '2'
    ast.pluralequation = '(n!=1)'
    ast.save()

#   Azərbaycan
#   Azerbaijani
    az, created = Language.objects.get_or_create(code='az')
    az.code_aliases='az-AZ'
    az.name = _(u'Azerbaijani')
    az.nplurals = '2'
    az.pluralequation = '(n != 1)'
    az.save()

#   Balochi (bal)
    bal, created = Language.objects.get_or_create(code='bal')
    bal.code_aliases='bal-IR'
    bal.name = _(u'Balochi')
    bal.save()

#   Беларуская
#   Belarusian
    be, created = Language.objects.get_or_create(code='be')
    be.code_aliases='be-BY'
    be.name = _(u'Belarusian')
    be.nplurals = '3'
    be.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    be.save()

#   Български
#   Bulgarian
    bg, created = Language.objects.get_or_create(code='bg')
    bg.code_aliases='bg-BG'
    bg.name = _(u'Bulgarian')
    bg.nplurals = '2'
    bg.pluralequation = '(n != 1)'
    bg.save()

#   বাংলা
#   Bengali
    bn, created = Language.objects.get_or_create(code='bn')
    bn.code_aliases='bn-BD'
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
    bo, created = Language.objects.get_or_create(code='bo')
    bo.code_aliases='bo-CN'
    bo.name = _(u'Tibetan')
    bo.nplurals = '1'
    bo.pluralequation = '0'
    bo.save()

#   Bosanski
#   Bosnian
    bs, created = Language.objects.get_or_create(code='bs')
    bs.code_aliases='bs-BA'
    bs.name = _(u'Bosnian')
    bs.nplurals = '3'
    bs.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    bs.save()

#   Català
#   Catalan
    ca, created = Language.objects.get_or_create(code='ca')
    ca.code_aliases='ca-ES'
    ca.name = _(u'Catalan (Valencian)')
    ca.nplurals = '2'
    ca.pluralequation = '(n != 1)'
    ca.save()

#   Česky
#   Czech
    cs, created = Language.objects.get_or_create(code='cs')
    cs.code_aliases='cs-CZ'
    cs.name = _(u'Czech')
    cs.nplurals = '3'
    cs.pluralequation = '(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2'
    cs.save()

#   Cymraeg
#   Welsh
    cy, created = Language.objects.get_or_create(code='cy')
    cy.code_aliases='cy-GB'
    cy.name = _(u'Welsh')
    cy.nplurals = '2'
    cy.pluralequation = '(n==2) ? 1 : 0'
    cy.save()

#   Dansk
#   Danish
    da, created = Language.objects.get_or_create(code='da')
    da.code_aliases='da-DK'
    da.name = _(u'Danish')
    da.nplurals = '2'
    da.pluralequation = '(n != 1)'
    da.save()

#   Deutsch
#   German
    de, created = Language.objects.get_or_create(code='de')
    de.code_aliases='de-DE'
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
    dz.code_aliases='dz-BT'
    dz.name = _(u'Dzongkha')
    dz.nplurals = '1'
    dz.pluralequation = '0'
    dz.save()

#   Ελληνικά
#   Greek
    el, created = Language.objects.get_or_create(code='el')
    el.code_aliases='el-GR'
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

#   English (United States)
    en_US, created = Language.objects.get_or_create(code='en_US')
    en_US.code_aliases='en-US'
    en_US.name = _(u'English (United States)')
    en_US.nplurals = '2'
    en_US.pluralequation = '(n != 1)'
    en_US.save()

#   English (South Africa)
    en_ZA, created = Language.objects.get_or_create(code='en_ZA')
    en_ZA.code_aliases = 'en-za en-ZA'
    en_ZA.name = _(u'English (South Africa)')
    en_ZA.nplurals = '2'
    en_ZA.pluralequation = '(n != 1)'
    en_ZA.save()

#   Esperanto
    eo, created = Language.objects.get_or_create(code='eo')
    eo.name = _(u'Esperanto')
    eo.nplurals = '2'
    eo.pluralequation = '(n!=1)'
    eo.save()

#   Español
#   Spanish
    es, created = Language.objects.get_or_create(code='es')
    es.code_aliases='es-ES'
    es.name = _(u'Spanish (Castilian)')
    es.nplurals = '2'
    es.pluralequation = '(n != 1)'
    es.save()

#   Argentinian Spanish
    es_ar, created = Language.objects.get_or_create(code='es_AR')
    es_ar.code_aliases='es-AR'
    es_ar.name = _(u'Spanish (Argentinian)')
    es_ar.nplurals = '2'
    es_ar.pluralequation = '(n != 1)'
    es_ar.save()

#   Mexican Spanish
    es_MX, created = Language.objects.get_or_create(code='es_MX')
    es_MX.code_aliases='es-mx es-MX'
    es_MX.name = _(u'Spanish (Mexican)')
    es_MX.nplurals = '2'
    es_MX.pluralequation = '(n != 1)'
    es_MX.save()

#   Eesti
#   Estonian
    et, created = Language.objects.get_or_create(code='et')
    et.code_aliases='et-EE'
    et.name = _(u'Estonian')
    et.nplurals = '2'
    et.pluralequation = '(n != 1)'
    et.save()

#   Euskara
#   Basque
    eu, created = Language.objects.get_or_create(code='eu')
    eu.code_aliases='eu-ES'
    eu.name = _(u'Basque')
    eu.nplurals = '2'
    eu.pluralequation = '(n != 1)'
    eu.save()

#   Persian
    fa, created = Language.objects.get_or_create(code='fa')
    fa.code_aliases='fa-IR'
    fa.name = _(u'Persian')
    fa.nplurals = '1'
    fa.pluralequation = '0'
    fa.save()

#   Suomi
#   Finnish
    fi, created = Language.objects.get_or_create(code='fi')
    fi.code_aliases='fi-FI'
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
    fr.code_aliases='fr-FR'
    fr.name = _(u'French')
    fr.nplurals = '2'
    fr.pluralequation = '(n > 1)'
    fr.save()

#   Furlan
#   Friulian
    fur, created = Language.objects.get_or_create(code='fur')
    fur.code_aliases='fur-IT'
    fur.name = _(u'Friulian')
    fur.nplurals = '2'
    fur.pluralequation = '(n != 1)'
    fur.save()

#   Frysk
#   Frisian
    fy, created = Language.objects.get_or_create(code='fy')
    fy.code_aliases='fy-NL'
    fy.name = _(u'Western Frisian')
    fy.nplurals = '2'
    fy.pluralequation = '(n != 1)'
    fy.save()

#   Gaeilge
#   Irish
    ga, created = Language.objects.get_or_create(code='ga')
    ga.code_aliases='ga-IE'
    ga.name = _(u'Irish')
    ga.nplurals = '5'
    ga.pluralequation = '(n==1 ? 0 : n==2 ? 1 : n<7 ? 2 : n<11 ? 3 : 4)'
    ga.save()

#   Galego
#   Galician
    gl, created = Language.objects.get_or_create(code='gl')
    gl.code_aliases='gl-ES'
    gl.name = _(u'Galician')
    gl.nplurals = '2'
    gl.pluralequation = '(n != 1)'
    gl.save()

#   ગુજરાતી
#   Gujarati
    gu, created = Language.objects.get_or_create(code='gu')
    gu.code_aliases='gu-IN'
    gu.name = _(u'Gujarati')
    gu.nplurals = '2'
    gu.pluralequation = '(n != 1)'
    gu.save()

#   Hebrew
    he, created = Language.objects.get_or_create(code='he')
    he.code_aliases='he-IL'
    he.name = _(u'Hebrew')
    he.nplurals = '2'
    he.pluralequation = '(n != 1)'
    he.save()

#   हिन्दी
#   Hindi
    hi, created = Language.objects.get_or_create(code='hi')
    hi.code_aliases='hi-IN'
    hi.name = _(u'Hindi')
    hi.nplurals = '2'
    hi.pluralequation = '(n != 1)'
    hi.save()

#   Hrvatski
#   Croatian
    hr, created = Language.objects.get_or_create(code='hr')
    hr.code_aliases='hr-HR'
    hr.name = _(u'Croatian')
    hr.nplurals = '3'
    hr.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    hr.save()

#   Haitian Creole
    ht, created = Language.objects.get_or_create(code='ht')
    ht.code_aliases='ht-HT'
    ht.name = _(u'Haitian (Haitian Creole)')
    ht.nplurals = '2'
    ht.pluralequation = '(n !=1)'
    ht.save()

#   Magyar
#   Hungarian
    hu, created = Language.objects.get_or_create(code='hu')
    hu.code_aliases='hu-HU'
    hu.name = _(u'Hungarian')
    hu.nplurals = '2'
    hu.pluralequation = '(n !=1)'
    hu.save()

#   Armenian
    hy, created = Language.objects.get_or_create(code='hy')
    hy.code_aliases='hy-AM'
    hy.name = _('Armenian')
    hy.save()

#   Bahasa Indonesia
#   Indonesian
    id, created = Language.objects.get_or_create(code='id')
    id.code_aliases='id-ID'
    id.name = _(u'Indonesian')
    id.nplurals = '1'
    id.pluralequation = '0'
    id.save()

#   Iloko
    ilo, created = Language.objects.get_or_create(code='ilo')
    ilo.code_aliases='ilo-PH'
    ilo.name = _('Iloko') 
    ilo.save()

#   Icelandic
    is_, created = Language.objects.get_or_create(code='is')
    is_.code_aliases='is-IS'
    is_.name = _(u'Icelandic')
    is_.nplurals = '2'
    is_.pluralequation = '(n != 1)'
    is_.save()

#   Italiano
#   Italian
    it, created = Language.objects.get_or_create(code='it')
    it.code_aliases='it-IT'
    it.name = _(u'Italian')
    it.nplurals = '2'
    it.pluralequation = '(n != 1)'
    it.save()

#   日本語
#   Japanese
    ja, created = Language.objects.get_or_create(code='ja')
    ja.code_aliases=' ja-jp ja-JP ja_JP'
    ja.name = _(u'Japanese')
    ja.nplurals = '1'
    ja.pluralequation = '0'
    ja.save()

#   ქართული
#   Georgian
    ka, created = Language.objects.get_or_create(code='ka')
    ka.code_aliases='ka-GE'
    ka.name = _(u'Georgian')
    ka.nplurals = '1'
    ka.pluralequation = '0'
    ka.save()

#   ភាសា
#   Khmer
    km, created = Language.objects.get_or_create(code='km')
    km.name = _(u'Khmer')
    km.nplurals = '1'
    km.pluralequation = '0'
    km.save() 

#   Kannada
    kn, created = Language.objects.get_or_create(code='kn')
    kn.code_aliases='kn-IN'
    kn.name = _('Kannada')
    kn.save() 

#   한국어
#   Korean
    ko, created = Language.objects.get_or_create(code='ko')
    ko.code_aliases='ko-KR'
    ko.name = _(u'Korean')
    ko.nplurals = '1'
    ko.pluralequation = '0'
    ko.save()

#   Kashmiri
    ks, created = Language.objects.get_or_create(code='ks')
    ks.code_aliases='ks-IN'
    ks.name = _(u'Kashmiri')
    ks.nplurals = '2'
    ks.pluralequation = '(n != 1)'
    ks.save()

#   Kurdî / كوردي
#   Kurdish
    ku, created = Language.objects.get_or_create(code='ku')
    ku.code_aliases='ku-IQ'
    ku.name = _(u'Kurdish')
    ku.nplurals = '2'
    ku.pluralequation = '(n != 1)'
    ku.save()

#   Kirgyz
    ky, created = Language.objects.get_or_create(code='ky')
    ky.name = _(u'Kirgyz')
    ky.nplurals = '1'
    ky.pluralequation = '(0)'
    ky.save()

#   Latin
    la, created = Language.objects.get_or_create(code='la')
    la.name = _(u'Latin')
    la.nplurals = '2'
    la.pluralequation = '(n!=1)'
    la.save()

#   Lëtzebuergesch
#   Letzeburgesch
#   lb.name = _(u'Letzeburgesch')
#   lb.nplurals = '2'
#   lb.pluralequation = '(n != 1)'

#   Lao
    lo, created = Language.objects.get_or_create(code='lo')
    lo.code_aliases='lo-LA'
    lo.name = _('Lao')
    lo.save()

#   Lietuvių
#   Lithuanian
    lt, created = Language.objects.get_or_create(code='lt')
    lt.code_aliases='lt-LT'
    lt.name = _(u'Lithuanian')
    lt.nplurals = '3'
    lt.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && (n%100<10 || n%100>=20) ? 1 : 2)'
    lt.save()

#   Latviešu
#   Latvian
    lv, created = Language.objects.get_or_create(code='lv')
    lv.code_aliases='lv-LV'
    lv.name = _(u'Latvian')
    lv.nplurals = '3'
    lv.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n != 0 ? 1 : 2)'
    lv.save()

#   Maithili
    mai, created = Language.objects.get_or_create(code='mai')
    mai.code_aliases='mai-IN'
    mai.name = _('Maithili')
    mai.save()

#   Macedonian
    mk, created = Language.objects.get_or_create(code='mk')
    mk.code_aliases='mk-MK'
    mk.name = _('Macedonian')
    mk.save()

#   Malayalam
    ml, created = Language.objects.get_or_create(code='ml')
    ml.code_aliases='ml-IN'
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
    mn.code_aliases='mn-MN'
    mn.name = _(u'Mongolian')
    mn.nplurals = '2'
    mn.pluralequation = '(n != 1)'
    mn.save()

#   Marathi
    mr, created = Language.objects.get_or_create(code='mr')
    mr.code_aliases='mr-IN'
    mr.name = _(u'Marathi')
    mr.nplurals = u'2'
    mr.pluralequation = u'(n != 1)'
    mr.save()

#   Malay
    ms, created = Language.objects.get_or_create(code='ms')
    ms.code_aliases='ms-MY'
    ms.name = _(u'Malay')
    ms.nplurals = u'1'
    ms.pluralequation = u'0'
    ms.save()

#   Malti
#   Maltese
    mt, created = Language.objects.get_or_create(code='mt')
    mt.code_aliases='mt-MT'
    mt.name = _(u'Maltese')
    mt.nplurals = '4'
    mt.pluralequation = '(n==1 ? 0 : n==0 || ( n%100>1 && n%100<11) ? 1 : (n%100>10 && n%100<20 ) ? 2 : 3)'
    mt.save()

#   Burmese
    my, created = Language.objects.get_or_create(code='my')
    my.code_aliases='my-MM'
    my.name = _('Burmese')
    my.save()

#   Nahuatl
#   nah.name = _(u'Nahuatl')
#   nah.nplurals = '2'
#   nah.pluralequation = '(n != 1)'

#   Bokmål
#   Norwegian Bokmål
    nb, created = Language.objects.get_or_create(code='nb')
    nb.code_aliases='nb-NO'
    nb.name = _('Norwegian Bokmål')
    nb.nplurals = '2'
    nb.pluralequation = '(n != 1)'
    nb.save()

#   Nepali\
    ne, created = Language.objects.get_or_create(code='ne')
    ne.code_aliases='ne-NP'
    ne.name = _(u'Nepali')
    ne.nplurals = u'2'
    ne.pluralequation = u'(n != 1)'
    ne.save()

#   Nederlands
#   Dutch
    nl, created = Language.objects.get_or_create(code='nl')
    nl.code_aliases='nl-NL'
    nl.name = _(u'Dutch (Flemish)')
    nl.nplurals = '2'
    nl.pluralequation = '(n != 1)'
    nl.save()

#   Nynorsk
#   Norwegian Nynorsk
    nn, created = Language.objects.get_or_create(code='nn')
    nn.code_aliases='nn-NO'
    nn.name = _(u'Norwegian Nynorsk')
    nn.nplurals = '2'
    nn.pluralequation = '(n != 1)'
    nn.save()

#   Norwegian
    no, created = Language.objects.get_or_create(code='no')
    no.code_aliases='no-NO'
    no.name = _('Norwegian')
    no.save()

#   Sesotho sa Leboa
#   Northern Sotho
    nso, created = Language.objects.get_or_create(code='nso')
    nso.code_aliases='nso-ZA'
    nso.name = _(u'Northern Sotho')
    nso.nplurals = '2'
    nso.pluralequation = '(n > 1)'
    nso.specialchars = 'šŠ'
    nso.save()

#   Oriya
    or_, created = Language.objects.get_or_create(code='or')
    or_.code_aliases='or-IN'
    or_.name = _(u'Oriya')
    or_.nplurals = '2'
    or_.pluralequation = '(n != 1)'
    or_.save()
    
#   Punjabi
    pa, created = Language.objects.get_or_create(code='pa')
    pa.code_aliases='pa-IN'
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
    pl.code_aliases='pl-PL'
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
    pt.code_aliases='pt-PT'
    pt.name = _(u'Portuguese')
    pt.nplurals = '2'
    pt.pluralequation = '(n != 1)'
    pt.save()

#   Português do Brasil
#   Portuguese (Brazilian)
    pt_BR, created = Language.objects.get_or_create(code='pt_BR')
    pt_BR.code_aliases = 'pt-br pt-BR'
    pt_BR.name = _(u'Portuguese (Brazilian)')
    pt_BR.nplurals = '2'
    pt_BR.pluralequation = '(n > 1)'
    pt_BR.save()

#   Română
#   Romanian
    ro, created = Language.objects.get_or_create(code='ro')
    ro.code_aliases='ro-RO'
    ro.name = _(u'Romanian')
    ro.nplurals = '3'
    ro.pluralequation = '(n==1 ? 0 : (n==0 || (n%100 > 0 && n%100 < 20)) ? 1 : 2);'
    ro.save()

#   Русский
#   Russian
    ru, created = Language.objects.get_or_create(code='ru')
    ru.code_aliases='ru-RU'
    ru.name = _(u'Russian')
    ru.nplurals = '3'
    ru.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    ru.save()

#   Sinhala
    si, created = Language.objects.get_or_create(code='si')
    si.code_aliases='si-LK'
    si.name = _('Sinhala')
    si.save()

#   Slovenčina
#   Slovak
    sk, created = Language.objects.get_or_create(code='sk')
    sk.code_aliases='sk-SK'
    sk.name = _(u'Slovak')
    sk.nplurals = '3'
    sk.pluralequation = '(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2'
    sk.save()

#   Slovenščina
#   Slovenian
    sl, created = Language.objects.get_or_create(code='sl')
    sl.code_aliases='sl-SI'
    sl.name = _(u'Slovenian')
    sl.nplurals = '4'
    sl.pluralequation = '(n%100==1 ? 0 : n%100==2 ? 1 : n%100==3 || n%100==4 ? 2 : 3)'
    sl.save()

#   Shqip
#   Albanian
    sq, created = Language.objects.get_or_create(code='sq')
    sq.code_aliases='sq-AL'
    sq.name = _(u'Albanian')
    sq.nplurals = '2'
    sq.pluralequation = '(n != 1)'
    sq.save()

#   Српски / Srpski
#   Serbian
    sr, created = Language.objects.get_or_create(code='sr')
    sr.code_aliases='sr-RS'
    sr.name = _(u'Serbian')
    sr.nplurals = '3'
    sr.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    sr.save()

#   Serbian
    srLatin, created = Language.objects.get_or_create(code='sr@latin')
    srLatin.code_aliases = 'sr@Latin sr@latn sr@Latn sr-Latn-RS sr-Latn sr_Latn'
    srLatin.name = _(u'Serbian (Latin)')
    srLatin.nplurals = '3'
    srLatin.pluralequation = '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    srLatin.save()


#   Sesotho
#   Sotho
    st, created = Language.objects.get_or_create(code='st')
    st.code_aliases='st-ZA'
    st.name = _(u'Sotho, Southern')
    st.nplurals = '2'
    st.pluralequation = '(n != 1)'
    st.save()

#   Svenska
#   Swedish
    sv, created = Language.objects.get_or_create(code='sv')
    sv.code_aliases='sv-SE'
    sv.name = _(u'Swedish')
    sv.nplurals = '2'
    sv.pluralequation = '(n != 1)'
    sv.save()

#   தமிழ்
#   Tamil
    ta, created = Language.objects.get_or_create(code='ta')
    ta.code_aliases='ta-IN'
    ta.name = _(u'Tamil')
    ta.nplurals = '2'
    ta.pluralequation = '(n != 1)'
    ta.save()

#   Telugu
    te, created = Language.objects.get_or_create(code='te')
    te.code_aliases='te-IN'
    te.name = _('Telugu')
    te.save()

#   Tajik
    tg, created = Language.objects.get_or_create(code='tg')
    tg.code_aliases='tg-TJ'
    tg.name = _('Tajik')
    tg.save()

#   Thai
    th, created = Language.objects.get_or_create(code='th')
    th.code_aliases='th-TH'
    th.name = _('Thai')
    th.save()

#   Tagalog
    tl, created = Language.objects.get_or_create(code='tl')
    tl.code_aliases='tl-PH'
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
    tr.code_aliases='tr-TR'
    tr.name = _(u'Turkish')
    tr.nplurals = '1'
    tr.pluralequation = '0'
    tr.save()

#   Urdu
    ur, created = Language.objects.get_or_create(code='ur')
    ur.code_aliases='ur-PK'
    ur.name = _('Urdu')
    ur.save()

#   Українська
#   Ukrainian
    uk, created = Language.objects.get_or_create(code='uk')
    uk.code_aliases='uk-UA'
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
    vi.code_aliases='vi-VN'
    vi.name = _(u'Vietnamese')
    vi.nplurals = '1'
    vi.pluralequation = '0'
    vi.save()

#   Wolof
    wo, created = Language.objects.get_or_create(code='wo')
    wo.code_aliases='wo-SN'
    wo.name = _(u'Wolof')
    wo.nplurals = '2'
    wo.pluralequation = '(n != 1)'
    wo.save()

#   Walon
#   Walloon
#   wa.name = _(u'Waloon')
#   wa.nplurals = '2'
#   wa.pluralequation = '(n > 1)'

#   Xhosa
    xh, created = Language.objects.get_or_create(code='xh')
    xh.name = _(u'Xhosa')
    xh.nplurals = '2'
    xh.pluralequation = '(n!=1)'
    xh.save()

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
    zu.code_aliases='zu-ZA'
    zu.name = _('Zulu')
    zu.save()
