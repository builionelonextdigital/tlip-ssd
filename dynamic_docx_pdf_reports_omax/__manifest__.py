# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": 'Dynamic Doc and Pdf Reports',
    "author": 'OMAX Informatics',
    "version": '1.0',
    "website": 'https://www.omaxinformatics.com',
    "category": 'Extra Tools,Productivity,Sales,Purchases,Accounting',
    'description': """
        Odoo app to design your own doc template and export the same to print the doc or pdf report.
    """,
    "depends": ['base'],
    "external_dependencies": {
        'python': [],
    },
    "data": [
        'security/ir.model.access.csv',
        'security/dynamic_docx_pdf_report_security.xml',
        'wizard/docx_template_wiz.xml',
        'views/docx_template.xml',
    ],
    "demo": [],
    "test": [],
    "images": ['static/description/banner.png',],
    "assets": {
    },
    "license": 'OPL-1',
    "currency": 'EUR',
    "price": 80,
    "installable": True,
    "auto_install": False,
    "application": True,
    "pre_init_hook": 'pre_init_check',
    "live_test_url": 'https://youtu.be/gaY95WFdbL0',
    "module_type": 'official',  # required bcz some time facing warning
    'summary': """
        Odoo app to design your own doc template and export the same to print the doc or pdf report.
        Design own doc template,Design own PDF template,
        Create many doc report for same model,
        Create many pdf report for same model,
        Dynamic doc reports,
        Dynamic pdf reports,
        Dynamic doc downloads,
        Dynamic pdf downloads,
        Design doc template for a report,
        Design Pdf template for a report,
        Print dynamic doc report,
        Print dynamic pdf report,
        Print doc for any odoo model,
        Print pdf for any odoo model, 
        Print doc for any odoo object, 
        Print pdf for any odoo object,
        App to print dynamic doc report,
        App to print dynamic pdf report,
        App to configure your own doc template,
        App to configure your own PDF template
        Design and print doc, 
        Design and print pdf,
        Design template for any model,
        Print doc for any model, 
        Print pdf for any model, 
        Design doc for any object, 
        Print doc for any object,
        Print pdf for any object,
        doc print, pdf print, doc print based on user,pdf print based on user, 
        Create Doc template, Doc template design,Create Pdf template, PDf template design,
        Odoo app to downlaod Doc report, Odoo app to downlaod PDF report,
        Odoo app to design Doc template,Odoo app to design Pdf template, Print report Doc,Print report Pdf,
        Configure template and print PDF,Configure template and print Doc, configure doc and print,configure pdf and print, Dynamic report doc,Dynamic report pdf, Dynamic report,
        configure report, design report, design Doc,design Pdf, configure Doc, configure PDf,dynamic report odoo, Dynamic, Doc,PDf, report,
        Preprinted report, dynamic preprinted report,
        Dynamic PDF report, Dynamic PDF reports, Design PDF reports, Print dynamic PDF reports, PDF reports, PDF, Configure PDF template,
        doc to pdf,print doc to pdf, download doc to pdf, Dynamic Sale order report, Dynamic Purchase order report, Dynamic Invoice report,
        Dynamic Inventory report, Dynamic Sale order pdf, Dynamic purchase order pdf, Dynamic Invoice pdf,Dynamic Inventory pdf,
        microsoft, microsoft word, libreoffice, libreoffice writer
French
-------
L'application Odoo pour concevoir votre propre modèle de document et l'exporter pour imprimer le document ou le rapport pdf.
        Créez votre propre modèle de document, créez votre propre modèle de PDF,
        Créer plusieurs rapports doc pour un même modèle,
        Créer plusieurs rapports PDF pour le même modèle,
        Rapports doc dynamiques,
        Rapports pdf dynamiques,
        Téléchargements dynamiques de documents,
        Téléchargements dynamiques de pdf,
        Concevoir un modèle de rapport doc,
        Concevoir un modèle Pdf pour un rapport,
        Imprimer un rapport doc dynamique,
        Imprimer un rapport pdf dynamique,
        Imprimer un document pour n'importe quel modèle odoo,
        Imprimer un pdf pour n'importe quel modèle odoo, 
        Imprimer un document pour n'importe quel objet odoo, 
        Imprimer un pdf pour n'importe quel objet odoo,
        Application pour l'impression d'un rapport pdf dynamique,
        Application pour imprimer un rapport pdf dynamique,
        Application pour configurer votre propre modèle de document,
        App pour configurer votre propre modèle de document, App pour configurer votre propre modèle de PDF
        Concevoir et imprimer des doc, 
        Concevoir et imprimer un pdf,
        Concevoir un modèle pour n'importe quel modèle,
        Imprimer un document pour n'importe quel modèle, 
        Imprimer un pdf pour n'importe quel modèle, 
        Conception d'un document pour n'importe quel objet, 
        Imprimez le document pour n'importe quel objet,
        Imprimer le pdf pour n'importe quel objet,
        Impression doc, impression pdf, impression doc en fonction de l'utilisateur, impression pdf en fonction de l'utilisateur, 
        Créer un modèle Doc, Conception d'un modèle Doc, Créer un modèle Pdf, Conception d'un modèle PDf,
        Odoo app to downlaod Doc report, Odoo app to downlaod PDF report, Odoo app to downlaod Doc report, Odoo app to downlaod PDF report,
        Odoo app to design Doc template,Odoo app to design Pdf template, Print report Doc,Print report Pdf,
        Configurer le modèle et imprimer le PDF, Configurer le modèle et imprimer le Doc, Configurer le doc et imprimer, Configurer le pdf et imprimer, Rapport dynamique doc, Rapport dynamique pdf, Rapport dynamique,
        configurer rapport, concevoir rapport, concevoir Doc, concevoir Pdf, configurer Doc, configurer PDf, rapport dynamique odoo, Dynamique, Doc, PDf, rapport,
        Rapport préimprimé, rapport préimprimé dynamique,
        Rapport PDF dynamique, Rapports PDF dynamiques, Concevoir des rapports PDF, Imprimer des rapports PDF dynamiques, Rapports PDF, PDF, Configurer un modèle PDF,
        Rapport dynamique de commande de vente, Rapport dynamique de commande d'achat, Rapport dynamique de facture,
        Rapport d'inventaire dynamique, Bon de vente dynamique pdf, Bon d'achat dynamique pdf, Facture dynamique pdf, Inventaire dynamique pdf,
Spanish
-------
Odoo aplicación para diseñar su propia plantilla doc y exportar el mismo para imprimir el informe doc o pdf.
        Diseñe su propia plantilla doc, Diseñe su propia plantilla PDF,
        Crear muchos informes doc para el mismo modelo,
        Crear muchos informes pdf para el mismo modelo,
        Informes de documentos dinámicos,
        Informes pdf dinámicos,
        Descargas de documentos dinámicos,
        Descargas pdf dinámicas,
        Diseñar plantilla doc para un informe,
        Diseñar plantilla Pdf para un informe,
        Imprimir informe doc dinámico,
        Imprimir informe pdf dinámico,
        Imprimir doc para cualquier modelo de odoo,
        Imprimir pdf para cualquier modelo de odoo, 
        Imprimir doc para cualquier objeto odoo, 
        Imprimir pdf para cualquier objeto odoo,
        App para imprimir informe doc dinámico,
        App para imprimir informe pdf dinámico,
        App para configurar su propia plantilla doc,
        Aplicación para configurar su propia plantilla PDF
        Diseñar e imprimir doc, 
        Diseñar e imprimir pdf,
        Diseñar plantilla para cualquier modelo,
        Imprimir doc para cualquier modelo, 
        Imprimir pdf para cualquier modelo, 
        Diseñar doc para cualquier objeto, 
        Imprimir doc para cualquier objeto,
        Imprimir pdf para cualquier objeto,
        Imprimir doc, Imprimir pdf, Imprimir doc según usuario, Imprimir pdf según usuario, 
        Crear Doc plantilla, Doc diseño de la plantilla,Crear Pdf plantilla, PDf diseño de la plantilla,
        Odoo app to downlaod Doc report, Odoo app to downlaod PDF report,
        Odoo app to design Doc template,Odoo app to design Pdf template, Imprimir informe Doc,Imprimir informe Pdf,
        Configurar plantilla e imprimir PDF,Configurar plantilla e imprimir Doc, configurar doc e imprimir,configurar pdf e imprimir, Informe dinámico doc,Informe dinámico pdf, Informe dinámico,
        configurar informe, diseñar informe, diseñar Doc,diseñar Pdf, configurar Doc, configurar PDf,informe dinámico odoo, Dinámico, Doc,PDf, informe,
        informe preimpreso, informe preimpreso dinámico,
        informe PDF dinámico, informes PDF dinámicos, diseñar informes PDF, imprimir informes PDF dinámicos, informes PDF, PDF, configurar plantilla PDF,
        doc to pdf,imprimir doc to pdf, descargar doc to pdf, Informe dinámico de pedido de venta, Informe dinámico de pedido de compra, Informe dinámico de factura,
        Informe dinámico de inventario, Informe dinámico de pedido de venta, Informe dinámico de pedido de compra, Informe dinámico de factura, Informe dinámico de inventario,
Chinese
-------
Odoo应用程序可以设计自己的文档模板，并导出相同的打印文档或PDF报告。
        设计自己的文档模板，设计自己的PDF模板、
        为同一模型创建许多文档报告、
        为同一模型创建许多pdf报告、
        动态文档报告、
        动态pdf报告、
        动态文档下载、
        动态pdf下载、
        设计报告的doc模板、
        为报告设计Pdf模板、
        打印动态文档报告、
        打印动态pdf报告、
        为任何odoo模型打印doc、
        为任何odoo模型打印pdf、 
        为任何odoo对象打印文档、 
        为任何odoo对象打印pdf、
        打印动态文档报告的应用程序、
        打印动态pdf报告的应用程序、
        应用来配置你自己的文档模板、
        应用程序配置您自己的PDF模板
        设计和打印文档、 
        设计和打印pdf、
        为任何模型设计模板、
        为任何模型打印文档、 
        为任何模型打印pdf、 
        为任何物体设计文档、 
        为任何对象打印文档、
        为任何对象打印pdf、
        文档打印，pdf打印，基于用户的文档打印，基于用户的pdf打印、 
        创建Doc模板，Doc模板设计，创建Pdf模板，PDf模板设计、
        Odoo应用下载Doc报告，Odoo应用下载PDF报告、
        Odoo应用程序设计Doc模板，Odoo应用程序设计Pdf模板，打印Doc报告，打印Pdf报告、
        配置模板并打印PDF，配置模板并打印Doc，配置Doc并打印，配置PDF并打印，动态报告DOC，动态报告PDF，动态报告、
        配置报告，设计报告，设计Doc，设计Pdf，配置Doc，配置PDf，动态报告odoo，动态，Doc，PDf，报告、
        预印报告，动态预印报告、
        动态PDF报告，动态PDF报告，设计PDF报告，打印动态PDF报告，PDF报告，PDF，配置PDF模板、
        doc转pdf，打印doc转pdf，下载doc转pdf，动态销售订单报告，动态采购订单报告，动态发票报告、
        动态库存报告，动态销售订单pdf，动态采购订单pdf，动态发票pdf，动态库存pdf、
Dutch
-----
Odoo-app om je eigen documentsjabloon te ontwerpen en hetzelfde te exporteren om het doc- of pdf-rapport af te drukken.
        Ontwerp je eigen doc sjabloon,Ontwerp je eigen PDF sjabloon,
        Maak veel documentrapporten voor hetzelfde model,
        Maak veel pdf-rapporten voor hetzelfde model,
        Dynamische doc rapporten,
        Dynamische pdf-rapporten,
        Dynamische doc downloads,
        Dynamische pdf downloads,
        Ontwerp doc sjabloon voor een rapport,
        Ontwerp pdf-sjabloon voor een rapport,
        Dynamisch doc rapport afdrukken,
        Dynamisch pdf rapport afdrukken,
        Doc afdrukken voor elk odoo-model,
        Print pdf voor elk odoo model, 
        Doc afdrukken voor elk odoo object, 
        Print pdf voor elk odoo object,
        App om dynamisch doc rapport af te drukken,
        App om dynamisch pdf rapport af te drukken,
        App om je eigen doc template te configureren,
        App om je eigen pdf sjabloon te configureren
        Ontwerp en print doc, 
        Ontwerp en print pdf,
        Ontwerp sjabloon voor elk model,
        Doc afdrukken voor elk model, 
        PDF afdrukken voor elk model, 
        Ontwerpdocument voor elk object, 
        Doc afdrukken voor elk object,
        pdf afdrukken voor elk object,
        doc afdrukken, pdf afdrukken, doc afdrukken op basis van gebruiker, pdf afdrukken op basis van gebruiker, 
        Doc sjabloon maken, Doc sjabloon ontwerpen, Pdf sjabloon maken, PDf sjabloon ontwerpen,
        Odoo-app om Doc-rapport te downloaden, Odoo-app om PDF-rapport te downloaden,
        Odoo app to design Doc template,Odoo app to design Pdf template, Print report Doc,Print report Pdf,
        Configureer sjabloon en print PDF,Configureer sjabloon en print Doc,Configureer doc en print,Configureer pdf en print,Dynamisch rapport doc,Dynamisch rapport pdf,Dynamisch rapport,
        rapport configureren, rapport ontwerpen, Doc ontwerpen, Pdf ontwerpen, Doc configureren, PDf configureren, dynamisch rapport odoo, Dynamisch, Doc, PDf, rapport configureren,
        Voorgedrukt rapport, dynamisch voorgedrukt rapport,
        Dynamisch PDF-rapport, dynamische PDF-rapporten, ontwerp PDF-rapporten, dynamische PDF-rapporten afdrukken, PDF-rapporten, PDF-sjabloon configureren,
        doc to pdf,doc to pdf afdrukken, doc to pdf downloaden, Dynamisch verkooporderrapport, Dynamisch inkooporderrapport, Dynamisch factuurrapport,
        Dynamisch voorraadrapport, Dynamische verkooporder pdf, Dynamische inkooporder pdf, Dynamische factuur pdf, Dynamische voorraad pdf,
German
------
Odoo-App zum Entwerfen Ihrer eigenen Dokumentvorlage und zum Exportieren derselben, um den Dokument- oder PDF-Bericht zu drucken.
        Eigene Dokumentvorlage entwerfen, eigene PDF-Vorlage entwerfen,
        Erstellen Sie viele Dokumentationsberichte für dasselbe Modell,
        Erstellen Sie viele PDF-Berichte für dasselbe Modell,
        Dynamische Doku-Berichte,
        Dynamische PDF-Berichte,
        Dynamische doc-Downloads,
        Dynamische pdf-Downloads,
        Entwurf einer doc-Vorlage für einen Bericht,
        Pdf-Vorlage für einen Bericht entwerfen,
        Dynamischen doc-Bericht drucken,
        Dynamischen pdf-Bericht drucken,
        Druck doc für jedes odoo Modell,
        Drucke pdf für jedes odoo Modell, 
        Drucke doc für jedes odoo Objekt, 
        Drucke pdf für jedes Odoo-Objekt,
        App zum Drucken von dynamischen doc-Berichten,
        App zum Drucken eines dynamischen pdf-Berichts,
        App zum Konfigurieren Ihrer eigenen Dokumentvorlage,
        App zum Konfigurieren Ihrer eigenen PDF-Vorlage
        Dokument entwerfen und drucken, 
        PDF entwerfen und drucken,
        Designvorlage für jedes Modell,
        Dokument für beliebiges Modell drucken, 
        PDF für beliebiges Modell drucken, 
        Entwurfsvorlage für beliebiges Objekt, 
        Druckvorlage für beliebiges Objekt,
        PDF für beliebiges Objekt drucken,
        doc print, pdf print, doc print based on user, pdf print based on user, 
        Doc-Vorlage erstellen, Doc-Vorlage entwerfen, Pdf-Vorlage erstellen, PDf-Vorlage entwerfen,
        Odoo-App zum Herunterladen von Doc-Berichten, Odoo-App zum Herunterladen von PDF-Berichten,
        Odoo app to design Doc template,Odoo app to design Pdf template, Print report Doc,Print report Pdf,
        Vorlage konfigurieren und PDF drucken, Vorlage konfigurieren und Doc drucken, Doc konfigurieren und drucken, PDF konfigurieren und drucken, Dynamischer Bericht doc, Dynamischer Bericht pdf, Dynamischer Bericht,
        Bericht konfigurieren, Bericht entwerfen, Doc entwerfen, Pdf entwerfen, Doc konfigurieren, PDf konfigurieren, Dynamischer Bericht odoo, Dynamisch, Doc, PDf, Bericht,
        Vorgedruckter Bericht, dynamischer vorgedruckter Bericht,
        Dynamischer PDF-Bericht, Dynamische PDF-Berichte, PDF-Berichte gestalten, Dynamische PDF-Berichte drucken, PDF-Berichte, PDF, PDF-Vorlage konfigurieren,
        doc to pdf, doc to pdf drucken, doc to pdf herunterladen, Dynamischer Verkaufsauftragsbericht, Dynamischer Bestellungsbericht, Dynamischer Rechnungsbericht,
        Dynamischer Lagerbestandsbericht, Dynamischer Verkaufsauftrag pdf, Dynamischer Einkaufsauftrag pdf, Dynamische Rechnung pdf, Dynamischer Lagerbestand pdf,
Indonesian
----------
Aplikasi Odoo untuk mendesain template dokumen Anda sendiri dan mengekspor yang sama untuk mencetak laporan dokumen atau pdf.
        Rancang templat dokumen sendiri, Rancang templat PDF sendiri,
        Buat banyak laporan dokumen untuk model yang sama,
        Buat banyak laporan pdf untuk model yang sama,
        Laporan dokumen dinamis,
        Laporan pdf dinamis,
        Unduhan dokumen dinamis,
        Unduhan pdf dinamis,
        Desain template dokumen untuk sebuah laporan,
        Desain template Pdf untuk sebuah laporan,
        Cetak laporan dokumen dinamis,
        Cetak laporan pdf dinamis,
        Cetak dokumen untuk model odoo apa pun,
        Cetak pdf untuk model odoo apa pun, 
        Cetak dokumen untuk objek odoo apa pun, 
        Cetak pdf untuk objek odoo apa pun,
        Aplikasi untuk mencetak laporan dokumen dinamis,
        Aplikasi untuk mencetak laporan pdf dinamis,
        Aplikasi untuk mengonfigurasi templat dokumen Anda sendiri,
        Aplikasi untuk mengonfigurasi template PDF Anda sendiri
        Desain dan cetak dokumen, 
        Desain dan cetak pdf,
        Templat desain untuk model apa pun,
        Cetak dokumen untuk model apa pun, 
        Cetak pdf untuk model apa pun, 
        Desain dokumen untuk objek apa pun, 
        Cetak dokumen untuk objek apa pun,
        Cetak pdf untuk objek apa pun,
        cetak dokumen, cetak pdf, cetak dokumen berdasarkan pengguna, cetak pdf berdasarkan pengguna, 
        Buat template Doc, desain template Doc, Buat template Pdf, desain template PDf,
        Aplikasi Odoo untuk mengunduh laporan Doc, aplikasi Odoo untuk mengunduh laporan PDF,
        Aplikasi Odoo untuk mendesain template Doc, aplikasi Odoo untuk mendesain template Pdf, Cetak laporan Doc, Cetak laporan Pdf,
        Konfigurasikan templat dan cetak PDF, Konfigurasikan templat dan cetak Doc, konfigurasikan doc dan cetak, konfigurasikan pdf dan cetak, Dokumen laporan dinamis, Laporan dinamis pdf, Laporan dinamis,
        konfigurasikan laporan, desain laporan, desain Doc, desain Pdf, konfigurasikan Doc, konfigurasikan PDf, laporan dinamis odoo, Dinamis, Doc, PDf, laporan,
        Laporan pracetak, laporan pracetak dinamis,
        Laporan PDF dinamis, Laporan PDF dinamis, Desain laporan PDF, Cetak laporan PDF dinamis, Laporan PDF, PDF, Konfigurasikan templat PDF,
        doc ke pdf, cetak doc ke pdf, unduh doc ke pdf, Laporan pesanan Penjualan Dinamis, Laporan pesanan Pembelian Dinamis, Laporan Faktur Dinamis,
        Laporan Persediaan Dinamis, pdf pesanan Penjualan Dinamis, pdf pesanan pembelian dinamis, pdf Faktur Dinamis, pdf Persediaan Dinamis,
Italy
------
Un'applicazione di Odoo per progettare il proprio modello di documento ed esportarlo per stampare il documento o il rapporto pdf.
        Progettare il proprio modello di documento, progettare il proprio modello di PDF,
        Creare molti documenti per lo stesso modello,
        Creare molti rapporti pdf per lo stesso modello,
        Rapporti dinamici su documenti,
        Rapporti pdf dinamici,
        Download dinamici di documenti,
        Download dinamici di pdf,
        Progettare un modello di documento per un rapporto,
        Progettare un modello Pdf per un rapporto,
        Stampa di rapporti dinamici in formato doc,
        Stampa di un rapporto pdf dinamico,
        Stampa doc per qualsiasi modello di odoo,
        Stampa pdf per qualsiasi modello di odoo, 
        Stampa doc per qualsiasi oggetto odoo, 
        Stampa pdf per qualsiasi oggetto odoo,
        App per stampare report di documenti dinamici,
        App per stampare rapporti dinamici in pdf,
        App per configurare il proprio modello di documento,
        App per configurare il proprio modello PDF
        Progettazione e stampa di documenti, 
        Progettare e stampare pdf,
        Modello di progettazione per qualsiasi modello,
        Stampa doc per qualsiasi modello, 
        Stampa pdf per qualsiasi modello, 
        Documento di progettazione per qualsiasi oggetto, 
        Stampa doc per qualsiasi oggetto,
        Stampa pdf per qualsiasi oggetto,
        stampa doc, stampa pdf, stampa doc in base all'utente, stampa pdf in base all'utente, 
        Creare modello Doc, progettare modello Doc, creare modello Pdf, progettare modello PDf,
        Applicazione Odoo per scaricare il rapporto Doc, Applicazione Odoo per scaricare il rapporto PDF,
        Progettazione di un modello Doc, progettazione di un modello Pdf, Stampa di un rapporto Doc, Stampa di un rapporto Pdf,
        Configura modello e stampa PDF, Configura modello e stampa Doc, configura doc e stampa, configura pdf e stampa, Report dinamico doc, Report dinamico pdf, Report dinamico,
        configurare report, progettare report, progettare Doc, progettare Pdf, configurare Doc, configurare PDf, report dinamico odoo, Dynamic, Doc, PDf, report,
        Rapporto prestampato, rapporto prestampato dinamico,
        Rapporto dinamico PDF, rapporti dinamici PDF, progettare rapporti PDF, stampare rapporti dinamici PDF, rapporti PDF, PDF, configurare modello PDF,
        doc to pdf, stampare doc to pdf, scaricare doc to pdf, report dinamico dell'ordine di vendita, report dinamico dell'ordine di acquisto, report dinamico della fattura,
        Rapporto sull'inventario dinamico, Rapporto sull'ordine di vendita dinamico, Rapporto sull'ordine di acquisto dinamico, Rapporto sulla fattura dinamica, Rapporto sull'inventario dinamico,
Korean
------
Odoo 앱을 사용하여 자신 만의 문서 템플릿을 디자인하고 동일한 템플릿을 내보내 문서 또는 pdf 보고서를 인쇄하십시오.
        나만의 문서 템플릿을 디자인하고, 나만의 PDF 템플릿을 디자인하세요,
        동일한 모델에 대해 많은 문서 보고서를 만듭니다,
        동일한 모델에 대해 많은 PDF 보고서를 만듭니다,
        동적 문서 보고서,
        동적 PDF 보고서,
        동적 문서 다운로드,
        동적 PDF 다운로드,
        보고서 용 문서 템플릿 디자인,
        보고서용 PDF 템플릿 디자인,
        동적 문서 보고서 인쇄,
        동적 PDF 보고서 인쇄,
        모든 odoo 모델에 대한 문서 인쇄,
        모든 odoo 모델에 대한 pdf 인쇄, 
        모든 odoo 개체에 대한 문서 인쇄, 
        모든 odoo 개체에 대한 pdf 인쇄,
        동적 문서 보고서를 인쇄하는 앱,
        동적 PDF 보고서를 인쇄하는 앱,
        나만의 문서 템플릿을 구성하는 앱,
        나만의 PDF 템플릿을 구성하는 앱
        문서 디자인 및 인쇄, 
        PDF 디자인 및 인쇄,
        모든 모델용 템플릿 디자인,
        모든 모델용 문서 인쇄, 
        모든 모델에 대한 PDF 인쇄, 
        모든 개체에 대한 문서 디자인, 
        모든 개체에 대한 문서 인쇄,
        모든 개체에 대한 pdf 인쇄,
        문서 인쇄, pdf 인쇄, 사용자 기반 문서 인쇄, 사용자 기반 pdf 인쇄, 
        문서 템플릿 만들기, 문서 템플릿 디자인, PDF 템플릿 만들기, PDf 템플릿 디자인,
        문서 보고서를 다운로드하는 Odoo 앱, PDF 보고서를 다운로드하는 Odoo 앱,
        문서 템플릿을 디자인하는 Odoo 앱, PDF 템플릿을 디자인하는 Odoo 앱, 보고서 문서 인쇄, 보고서 PDF 인쇄,
        템플릿 구성 및 PDF 인쇄, 템플릿 구성 및 인쇄 문서, 문서 구성 및 인쇄, PDF 구성 및 인쇄, 동적 보고서 문서, 동적 보고서 pdf, 동적 보고서,
        보고서 구성, 디자인 보고서, 디자인 문서, 디자인 PDF, 문서 구성, PDf 구성, 동적 보고서 오두, 동적, 문서, PDf, 보고서,
        미리 인쇄된 보고서, 동적 미리 인쇄된 보고서,
        동적 PDF 보고서, 동적 PDF 보고서, 동적 PDF 보고서 디자인, 동적 PDF 보고서 인쇄, PDF 보고서, PDF, PDF 템플릿 구성,
        문서를 PDF로, 문서를 PDF로 인쇄, 문서를 PDF로 다운로드, 동적 판매 주문 보고서, 동적 구매 주문 보고서, 동적 송장 보고서,
        동적 재고 보고서, 동적 판매 주문 pdf, 동적 구매 주문 pdf, 동적 송장 pdf, 동적 인보이스 pdf, 동적 재고 pdf,
Japanese
--------
Odooアプリは独自のドキュメントテンプレートをデザインし、ドキュメントやPDFレポートを印刷するために同じものをエクスポートします。
        独自のドキュメントテンプレート、独自のPDFテンプレートをデザインします、
        同じモデルのドキュメントレポートを多数作成
        同じモデルのPDFレポートを多数作成
        ダイナミックなdocレポート、
        動的pdfレポート、
        動的docダウンロード、
        動的pdfダウンロード
        報告書のdocテンプレートをデザインする、
        報告書のPDFテンプレートをデザインする
        動的docレポートの印刷、
        ダイナミックpdfレポートの印刷、
        あらゆるODOOモデルのドキュメントを印刷、
        あらゆるodooモデルにpdfを印刷、 
        あらゆるodooオブジェクトにドキュメントを印刷、 
        あらゆるodooオブジェクトのpdfを印刷、
        ダイナミックドキュメントレポートを印刷するアプリ、
        ダイナミックpdfレポート印刷アプリ、
        独自のdocテンプレートを設定するアプリ
        独自のPDFテンプレートを設定するアプリ
        ドキュメントをデザインして印刷する 
        PDFをデザインして印刷する
        どんなモデルにも対応するデザインテンプレート
        あらゆるモデルのドキュメントを印刷、 
        どんなモデルにもpdfを印刷 
        あらゆるオブジェクトのデザインドキュメント 
        どんなオブジェクトにもドキュメントを印刷、
        どんなオブジェクトにもpdfを印刷します、
        doc print, pdf print, doc print based on user, pdf print based on user、 
        Docテンプレートの作成、Docテンプレートのデザイン、Pdfテンプレートの作成、PDfテンプレートのデザイン、
        OdooアプリでDocレポートをダウンロード, OdooアプリでPDFレポートをダウンロード、
        OdooアプリでDocテンプレートをデザイン,OdooアプリでPdfテンプレートをデザイン, Docレポートを印刷,Pdfレポートを印刷、
        テンプレートを設定してPDFを印刷,テンプレートを設定してDocを印刷,Docを設定して印刷,PDFを設定して印刷,ダイナミックレポートDoc,ダイナミックレポートPDF,ダイナミックレポート、
        設定レポート、デザインレポート、デザインDoc、デザインPdf、設定Doc、設定PDf、ダイナミックレポートodoo、ダイナミック、Doc、PDf、レポート、
        プレプリントレポート, ダイナミックプレプリントレポート、
        ダイナミックPDFレポート, ダイナミックPDFレポート, PDFレポートのデザイン, ダイナミックPDFレポートの印刷, PDFレポート, PDF, PDFテンプレートの設定、
        動的販売注文レポート、動的購買注文レポート、動的請求書レポート、
        ダイナミック在庫レポート、ダイナミック販売注文PDF、ダイナミック購入注文PDF、ダイナミック請求書PDF、ダイナミック在庫PDF、
Portugese
--------
Aplicação Odoo para conceber o seu próprio modelo de documento e exportá-lo para imprimir o documento ou o relatório em PDF.
        Conceber o seu próprio modelo de documento, conceber o seu próprio modelo de PDF,
        Criar vários relatórios de documentos para o mesmo modelo,
        Criar muitos relatórios PDF para o mesmo modelo,
        Relatórios dinâmicos de documentos,
        Relatórios PDF dinâmicos,
        Transferências dinâmicas de documentos,
        Transferências dinâmicas de pdf,
        Conceber um modelo de documento para um relatório,
        Conceber um modelo de PDF para um relatório,
        Imprimir relatório dinâmico de documentos,
        Imprimir relatório dinâmico em pdf,
        Imprimir doc para qualquer modelo odoo,
        Imprimir pdf para qualquer modelo odoo, 
        Imprimir documento para qualquer objeto odoo, 
        Imprimir pdf para qualquer objeto odoo,
        Aplicação para imprimir relatório dinâmico de documentos,
        Aplicação para imprimir um relatório dinâmico em pdf,
        Aplicação para configurar o seu próprio modelo de documento,
        Aplicação para configurar o seu próprio modelo de PDF
        Conceber e imprimir doc, 
        Conceber e imprimir pdf,
        Conceber um modelo para qualquer modelo,
        Imprimir documento para qualquer modelo, 
        Imprimir pdf para qualquer modelo, 
        Conceber documento para qualquer objeto, 
        Imprimir documento para qualquer objeto,
        Imprimir pdf para qualquer objeto,
        Impressão de documentos, impressão de pdf, impressão de documentos com base no utilizador, impressão de pdf com base no utilizador, 
        Criar modelo de documento, conceção de modelo de documento, criar modelo de pdf, conceção de modelo de pdf,
        Aplicação Odoo para descarregar o relatório Doc, aplicação Odoo para descarregar o relatório PDF,
        Aplicação Odoo para conceber modelo de documento, Aplicação Odoo para conceber modelo de PDF, Imprimir relatório Doc, Imprimir relatório Pdf,
        Configurar modelo e imprimir PDF, Configurar modelo e imprimir Doc, configurar doc e imprimir, configurar pdf e imprimir, Relatório dinâmico doc, Relatório dinâmico pdf, Relatório dinâmico,
        configurar relatório, conceber relatório, conceber Doc, conceber Pdf, configurar Doc, configurar PDf, relatório dinâmico odoo, Dinâmico, Doc, PDf, relatório,
        Relatório pré-impresso, relatório pré-impresso dinâmico,
        Relatório PDF dinâmico, Relatórios PDF dinâmicos, Conceber relatórios PDF, Imprimir relatórios PDF dinâmicos, Relatórios PDF, PDF, Configurar modelo PDF,
        doc para pdf, imprimir doc para pdf, descarregar doc para pdf, relatório dinâmico de ordem de venda, relatório dinâmico de ordem de compra, relatório dinâmico de faturação,
        Relatório de inventário dinâmico, pdf de ordem de venda dinâmica, pdf de ordem de compra dinâmica, pdf de fatura dinâmica, pdf de inventário dinâmico,
Russian
-------
Приложение Odoo для разработки собственного шаблона документа и экспорта этого шаблона для печати документа или отчета в формате pdf.
        Разработка собственного шаблона документа, разработка собственного шаблона PDF,
        Создание множества отчетов в формате doc для одной модели,
        Создание множества отчетов в формате pdf для одной модели,
        Динамические отчеты в формате doc,
        Динамические отчеты в формате pdf,
        Динамические загрузки документов,
        Динамические загрузки pdf,
        Разработать шаблон doc для отчета,
        Разработать шаблон Pdf для отчета,
        Печать динамического отчета doc,
        Печать динамического отчета в формате pdf,
        Печать doc для любой модели odoo,
        Печать pdf для любой модели odoo, 
        Печать doc для любого объекта odoo, 
        Печать pdf для любого объекта odoo,
        Приложение для печати динамического отчета в формате doc,
        Приложение для печати динамического отчета в формате pdf,
        Приложение для настройки собственного шаблона doc,
        Приложение для настройки собственного шаблона PDF
        Разработка и печать doc, 
        Дизайн и печать pdf,
        Дизайн шаблона для любой модели,
        Печать doc для любой модели, 
        Печать pdf для любой модели, 
        Дизайн doc для любого объекта, 
        Печать doc для любого объекта,
        Печать pdf для любого объекта,
        печать doc, печать pdf, печать doc на основе пользователя, печать pdf на основе пользователя, 
        Создание шаблона Doc, дизайн шаблона Doc, создание шаблона Pdf, дизайн шаблона PDf,
        Приложение Odoo для загрузки отчета Doc, приложение Odoo для загрузки отчета PDF,
        Приложение Odoo для разработки шаблона Doc, Приложение Odoo для разработки шаблона Pdf, Печать отчета Doc, Печать отчета Pdf,
        Настроить шаблон и печать PDF,Настроить шаблон и печать Doc,Настроить doc и печать,Настроить pdf и печать,Динамический отчет doc,Динамический отчет pdf,Динамический отчет,
        настроить отчет, дизайн отчета, дизайн Doc, дизайн Pdf, настроить Doc, настроить PDf, динамический отчет odoo, Dynamic, Doc, PDf, report,
        Предварительно напечатанный отчет, динамический предварительно напечатанный отчет,
        Динамический PDF отчет, Динамические PDF отчеты, Дизайн PDF отчетов, Печать динамических PDF отчетов, PDF отчеты, PDF, Настроить PDF шаблон,
        doc в pdf, печать doc в pdf, скачать doc в pdf, динамический отчет по заказу на продажу, динамический отчет по заказу на покупку, динамический отчет по счету-фактуре,
        Динамический отчет по инвентаризации, Динамический заказ на продажу pdf, Динамический заказ на покупку pdf, Динамический счет-фактура pdf, Динамическая инвентаризация pdf,
Turkish
--------
Kendi doküman şablonunuzu tasarlamak ve dokümanı veya pdf raporunu yazdırmak için aynısını dışa aktarmak için Odoo uygulaması.
        Kendi doküman şablonunu tasarlayın, Kendi PDF şablonunu tasarlayın,
        Aynı model için birçok doküman raporu oluşturun,
        Aynı model için birçok pdf raporu oluşturun,
        Dinamik doküman raporları,
        Dinamik pdf raporları,
        Dinamik doküman indirmeleri,
        Dinamik pdf indirmeleri,
        Bir rapor için doküman şablonu tasarlayın,
        Bir rapor için Pdf şablonu tasarlayın,
        Dinamik doküman raporu yazdırın,
        Dinamik pdf raporu yazdırın,
        Herhangi bir odoo modeli için doküman yazdırın,
        Herhangi bir odoo modeli için pdf yazdırın, 
        Herhangi bir odoo nesnesi için doküman yazdırın, 
        Herhangi bir odoo nesnesi için pdf yazdırın,
        Dinamik doküman raporu yazdırmak için uygulama,
        Dinamik pdf raporu yazdırmak için uygulama,
        Kendi doküman şablonunuzu yapılandırmak için uygulama,
        Kendi PDF şablonunuzu yapılandırmak için uygulama
        Tasarım ve baskı dokümanı, 
        Tasarım ve baskı pdf,
        Herhangi bir model için tasarım şablonu,
        Herhangi bir model için doküman yazdırın, 
        Herhangi bir model için pdf yazdırın, 
        Herhangi bir nesne için tasarım dokümanı, 
        Herhangi bir nesne için doküman yazdırın,
        Herhangi bir nesne için pdf yazdırın,
        doc yazdırma, pdf yazdırma, kullanıcıya göre doc yazdırma, kullanıcıya göre pdf yazdırma, 
        Doc şablonu oluştur, Doc şablon tasarımı, Pdf şablonu oluştur, PDf şablon tasarımı,
        Doc raporunu indirmek için Odoo uygulaması, PDF raporunu indirmek için Odoo uygulaması,
        Doküman şablonu tasarlamak için Odoo uygulaması, Pdf şablonu tasarlamak için Odoo uygulaması, Doküman raporu yazdır, Pdf raporu yazdır,
        Şablonu yapılandırın ve PDF yazdırın, Şablonu yapılandırın ve Doc yazdırın, doc yapılandırın ve yazdırın, pdf yapılandırın ve yazdırın, Dinamik rapor doc, Dinamik rapor pdf, Dinamik rapor,
        rapor yapılandırma, rapor tasarlama, Doc tasarlama, Pdf tasarlama, Doc yapılandırma, PDf yapılandırma, dinamik rapor odoo, Dinamik, Doc,PDf, rapor,
        Önceden basılmış rapor, dinamik önceden basılmış rapor,
        Dinamik PDF raporu, Dinamik PDF raporları, PDF raporları tasarlayın, Dinamik PDF raporlarını yazdırın, PDF raporları, PDF, PDF şablonunu yapılandırın,
        doc to pdf,print doc to pdf, download doc to pdf, Dynamic Sale order report, Dynamic Purchase order report, Dynamic Invoice report,
        Dinamik Envanter raporu, Dinamik Satış siparişi pdf, Dinamik satın alma siparişi pdf, Dinamik Fatura pdf, Dinamik Envanter pdf,
Ukrainian
--------
Додаток Odoo для створення власного шаблону документу та експорту його для друку документу або звіту у форматі pdf.
        Створіть власний шаблон документа, створіть власний шаблон PDF,
        Створіть багато звітів у форматі doc для однієї моделі,
        Створіть багато PDF-звітів для однієї моделі,
        Динамічні звіти у форматі doc,
        Динамічні PDF-звіти,
        Динамічні завантаження документів,
        Динамічні завантаження pdf,
        Створіть шаблон документа для звіту,
        Створіть шаблон PDF для звіту,
        Друк динамічного звіту doc,
        Надрукуйте динамічний звіт у форматі pdf,
        Друк doc для будь-якої моделі odoo,
        Роздрукувати pdf для будь-якої моделі odoo, 
        Роздрукувати doc для будь-якого об'єкта odoo, 
        Роздрукувати pdf для будь-якого об'єкта odoo,
        Додаток для друку динамічного звіту doc,
        Додаток для друку динамічного звіту у форматі pdf,
        Додаток для налаштування власного шаблону doc,
        Додаток для налаштування власного шаблону PDF
        Створення та друк doc, 
        Створення та друк pdf,
        Створення шаблону для будь-якої моделі,
        Друк doc для будь-якої моделі, 
        Друк pdf для будь-якої моделі, 
        Створити документ для будь-якого об'єкта, 
        Роздрукувати документ для будь-якого об'єкта,
        Друк pdf для будь-якого об'єкта,
        друк doc, друк pdf, друк doc на основі користувача, друк pdf на основі користувача, 
        Створити шаблон Doc, Дизайн шаблону Doc, Створити шаблон Pdf, Дизайн шаблону PDf,
        Додаток Odoo для завантаження звіту Doc, додаток Odoo для завантаження звіту PDF,
        Додаток Odoo для створення шаблону Doc, Додаток Odoo для створення шаблону Pdf, Друк звіту Doc, Друк звіту Pdf,
        Налаштувати шаблон і роздрукувати PDF, Налаштувати шаблон і роздрукувати Doc, Налаштувати doc і роздрукувати, Налаштувати pdf і роздрукувати, Динамічний звіт doc, Динамічний звіт pdf, Динамічний звіт,
        налаштувати звіт, дизайн звіту, дизайн Doc, дизайн Pdf, налаштувати Doc, налаштувати PDf, динамічний звіт odoo, динамічний, Doc, PDf, звіт,
        Попередньо надрукований звіт, динамічний попередньо надрукований звіт,
        Динамічний PDF-звіт, Динамічні PDF-звіти, Дизайн PDF-звітів, Друк динамічних PDF-звітів, PDF-звіти, PDF, Налаштувати шаблон PDF,
        doc to pdf, друк doc to pdf, завантажити doc to pdf, Динамічний звіт про замовлення на продаж, Динамічний звіт про замовлення на купівлю, Динамічний звіт про рахунки-фактури,
        Динамічний інвентаризаційний звіт, Динамічні замовлення на продаж pdf, Динамічні замовлення на покупку pdf, Динамічні рахунки-фактури pdf, Динамічні інвентаризаційні звіти pdf,
Swedish
-------
Odoo-app för att designa din egen dokumentmall och exportera densamma för att skriva ut dokumentet eller pdf-rapporten.
        Designa egen dokumentmall,Designa egen PDF-mall,
        Skapa många dokumentrapporter för samma modell,
        Skapa många pdf-rapporter för samma modell,
        Dynamiska dokumentrapporter,
        Dynamiska pdf-rapporter,
        Dynamiska dokumentnedladdningar,
        Dynamiska pdf-nedladdningar,
        Designa doc-mall för en rapport,
        Utforma pdf-mall för en rapport,
        Skriv ut dynamisk doc-rapport,
        Skriv ut dynamisk pdf-rapport,
        Skriv ut doc för alla odoo-modeller,
        Skriv ut pdf för alla odoo-modeller, 
        Skriv ut doc för alla odoo-objekt, 
        Skriv ut pdf för alla odoo-objekt,
        App för att skriva ut dynamisk doc-rapport,
        App för att skriva ut dynamisk pdf-rapport,
        App för att konfigurera din egen dokumentmall,
        App för att konfigurera din egen PDF-mall
        Designa och skriv ut dokument, 
        Designa och skriv ut pdf,
        Designmall för valfri modell,
        Skriv ut dokument för alla modeller, 
        Skriv ut pdf för valfri modell, 
        Designdokument för valfritt objekt, 
        Skriv ut dokument för valfritt objekt,
        Skriv ut pdf för valfritt objekt,
        utskrift av dokument, utskrift av pdf, utskrift av dokument baserat på användare, utskrift av pdf baserat på användare, 
        Skapa Doc-mall, design av Doc-mall,Skapa Pdf-mall, design av PDf-mall,
        Odoo-app för att ladda ner Doc-rapport, Odoo-app för att ladda ner PDF-rapport,
        Odoo-app för att designa Doc-mall,Odoo-app för att designa Pdf-mall, Skriv ut rapport Doc,Skriv ut rapport Pdf,
        Konfigurera mall och skriv ut PDF,Konfigurera mall och skriv ut Doc, konfigurera doc och skriv ut,konfigurera pdf och skriv ut, Dynamisk rapport doc,Dynamisk rapport pdf, Dynamisk rapport,
        konfigurera rapport, designa rapport, designa Doc,designa Pdf, konfigurera Doc, konfigurera PDf,dynamisk rapport odoo, Dynamisk, Doc,PDf, rapport,
        Förtryckt rapport, dynamisk förtryckt rapport,
        Dynamisk PDF-rapport, Dynamiska PDF-rapporter, Utforma PDF-rapporter, Skriv ut dynamiska PDF-rapporter, PDF-rapporter, PDF, Konfigurera PDF-mall,
        doc to pdf,print doc to pdf, download doc to pdf, Dynamisk försäljningsorderrapport, Dynamisk inköpsorderrapport, Dynamisk fakturarapport,
        Dynamisk lagerrapport, Dynamisk försäljningsorder pdf, Dynamisk inköpsorder pdf, Dynamisk faktura pdf, Dynamisk lager pdf,
Arabic
-------
تطبيق Odoo لتصميم قالب المستند الخاص بك وتصديره لطباعة تقرير doc أو pdf.
         تصميم قالب مستند خاص ، تصميم قالب PDF خاص ،
         إنشاء العديد من تقارير المستندات لنفس النموذج ،
         إنشاء العديد من تقارير pdf لنفس النموذج ،
         تقارير المستندات الديناميكية ،
         تقارير pdf الديناميكية ،
         تنزيلات المستندات الديناميكية ،
         تنزيلات pdf الديناميكية ،
         قالب مستند التصميم لتقرير ،
         قالب تصميم Pdf لتقرير ،
         طباعة تقرير مستند ديناميكي ،
         طباعة تقرير pdf الديناميكي ،
         طباعة المستند لأي طراز أودو ،
         طباعة ملف pdf لأي طراز أودو ،
         طباعة مستند لأي كائن odoo ،
         طباعة pdf لأي كائن odoo ،
         تطبيق لطباعة تقرير مستند ديناميكي ،
         تطبيق لطباعة تقرير pdf الديناميكي ،
         التطبيق لتكوين قالب المستند الخاص بك ،
         التطبيق لتكوين قالب PDF الخاص بك
         تصميم وطباعة المستند ،
         تصميم وطباعة pdf ،
         قالب تصميم لأي نموذج ،
         طباعة المستند لأي طراز ،
         طباعة pdf لأي طراز ،
         مستند التصميم لأي كائن ،
         طباعة مستند لأي كائن ،
         طباعة pdf لأي كائن ،
         طباعة doc ، طباعة pdf ، طباعة doc بناءً على المستخدم ، طباعة pdf بناءً على المستخدم ،
         إنشاء قالب Doc ، تصميم قالب Doc ، إنشاء قالب Pdf ، تصميم قالب PDf ،
         تطبيق Odoo لتنزيل تقرير Doc ، وتطبيق Odoo لتنزيل تقرير PDF ،
         تطبيق Odoo لتصميم قالب Doc ، تطبيق Odoo لتصميم قالب Pdf ، طباعة تقرير Doc ، طباعة تقرير Pdf ،
         تكوين القالب وطباعة PDF ، تكوين القالب وطباعة المستند ، تكوين المستند والطباعة ، تكوين pdf والطباعة ، مستند التقرير الديناميكي ، تقرير pdf الديناميكي ، التقرير الديناميكي ،
         تكوين تقرير ، تقرير تصميم ، مستند تصميم ، تصميم ملف PDF ، تكوين مستند ، تكوين PDf ، تقرير ديناميكي odoo ، ديناميكي ، مستند ، PDf ، تقرير ،
         تقرير مطبوع مسبقًا ، تقرير ديناميكي مطبوع مسبقًا ،
         تقرير PDF الديناميكي ، تقارير PDF الديناميكية ، تصميم تقارير PDF ، طباعة تقارير PDF الديناميكية ، تقارير PDF ، PDF ، تكوين قالب PDF ،
         doc إلى pdf ، وطباعة المستند إلى pdf ، وتنزيل المستند إلى pdf ، وتقرير أمر البيع الديناميكي ، وتقرير أمر الشراء الديناميكي ، وتقرير الفاتورة الديناميكية ،
         تقرير المخزون الديناميكي ، أمر البيع الديناميكي pdf ، أمر الشراء الديناميكي pdf ، الفاتورة الديناميكية pdf ، المخزون الديناميكي pdf ،
Persian
-------
برنامه Odoo برای طراحی الگوی سند خود و صادر کردن آن برای چاپ گزارش سند یا pdf.
         طراحی قالب سند خود، طراحی قالب PDF خود،
         ایجاد بسیاری از گزارشات سند برای همان مدل،
         ایجاد بسیاری از گزارش های پی دی اف برای همان مدل،
         گزارشات داینامیک داک،
         گزارش های pdf پویا،
         بارگیری اسناد پویا،
         دانلود پویا پی دی اف،
         طراحی قالب سند برای گزارش،
         طراحی قالب پی دی اف برای گزارش،
         چاپ گزارش سند پویا،
         چاپ گزارش پویا pdf،
         چاپ سند برای هر مدل اودو،
         چاپ pdf برای هر مدل odoo،
         چاپ سند برای هر شی odoo،
         چاپ pdf برای هر شی odoo،
         برنامه برای چاپ گزارش سند پویا،
         برنامه برای چاپ گزارش پویا pdf،
         برنامه برای پیکربندی الگوی سند خود،
         برنامه ای برای پیکربندی قالب PDF خود
         طراحی و چاپ سند،
         طراحی و چاپ pdf،
         طراحی قالب برای هر مدل،
         چاپ سند برای هر مدل،
         چاپ pdf برای هر مدلی،
         طراحی سند برای هر شی،
         چاپ سند برای هر شی،
         چاپ pdf برای هر شی،
         چاپ doc، چاپ پی دی اف، چاپ سند بر اساس کاربر، چاپ پی دی اف بر اساس کاربر،
         ایجاد قالب Doc، طراحی قالب Doc، ایجاد قالب پی دی اف، طراحی قالب پی دی اف،
         برنامه Odoo برای دانلود گزارش Doc، برنامه Odoo برای دانلود گزارش PDF،
         برنامه Odoo برای طراحی قالب Doc، برنامه Odoo برای طراحی قالب Pdf، چاپ گزارش Doc، چاپ گزارش Pdf،
         پیکربندی قالب و چاپ PDF، پیکربندی الگو و چاپ Doc، پیکربندی سند و چاپ، پیکربندی pdf و چاپ، سند گزارش پویا، گزارش پویا pdf، گزارش پویا،
         پیکربندی گزارش، گزارش طراحی، طراحی Doc، طراحی پی دی اف، پیکربندی Doc، پیکربندی PDf، گزارش پویا odoo، Dynamic، Doc، PDF، گزارش،
         گزارش از پیش چاپ شده، گزارش از پیش چاپ شده پویا،
         گزارش پویا PDF، گزارش پویا PDF، طراحی گزارش های PDF، چاپ گزارش های PDF پویا، گزارش های PDF، PDF، پیکربندی قالب PDF،
         doc به pdf، چاپ سند به pdf، دانلود سند به pdf، گزارش سفارش فروش پویا، گزارش سفارش خرید پویا، گزارش فاکتور پویا،
         گزارش موجودی پویا، pdf سفارش فروش پویا، pdf سفارش خرید پویا، pdf فاکتور پویا، pdf موجودی پویا،
	""",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
