# Review: Molecular cloning and sequence analysis of Factor C cDNA from the Singapore horseshoe crab, Carcinoscorpius rotundicauda

Source: https://doi.org/None  (PMID 7538401, Molecular Marine Biology and Biotechnology 1995)

> Check each item against the paper. To fix something, just say so (e.g. "AC4 stance should be neutral") and I'll edit the JSON and regenerate this. Approve when it's right.

## ⚠ Review priorities (the verifier flagged these)

- **NC2** [THEORETICAL (not experimentally shown), verify, low-conf 0.6] — The two CrFC cDNA forms arise from differential splicing of the primary transcript around its 5' terminus.
- **NC3** [THEORETICAL (not experimentally shown), verify, low-conf 0.45] — Recombinant C. rotundicauda Factor C is commercially significant as the basis of a rapid endotoxin-detection kit for pharmaceutical QA.
- **NC4** [THEORETICAL (not experimentally shown), verify, figure-only data, low-conf 0.4] — CrFC21 constructs express more Factor C than CrFC26 in vitro (absence of false-start ATGs, accessible AUG, Kozak consensus).
- **NC5** [THEORETICAL (not experimentally shown), verify, low-conf 0.4] — C. rotundicauda amoebocyte lysate is reportedly more sensitive to endotoxin than Limulus or Tachypleus lysates (Kim et al. 1988).

- **Conflict of interest:** declared *not stated (1995 paper)*; academic (NUS) authors; NOT employed by a reagent manufacturer; BUT disclose a 'patent pending' on the favoured CrFC21 expression construct (NC4)

## Methods (13)

- **M1** Amoebocyte procurement & total/poly(A)+ RNA preparation
- **M2** Directional cDNA synthesis and cloning into lambda-gt22
- **M3** Library screening / plaque hybridization (heterologous TtFC53 probe)
- **M4** Restriction mapping of CrFC clones
- **M5** Subcloning EE and EN fragments into pGEM 11Zf(+)
- **M6** DNA sequencing (Sanger dideoxy, both strands) with exonuclease deletions
- **M7** Northern blot analysis of amoebocyte RNA
- **M8** Southern blot hybridization of CrFC clones
- **M9** EMBL gene-bank homology search of catalytic domain
- **M10** Computational mRNA secondary-structure prediction of 5' UTR
- **M11** Kyte-Doolittle hydropathy analysis of N-terminus
- **M12** In vitro transcription-coupled-translation (TnT) expression assay
- **M13** Domain / catalytic-triad structural annotation by homology

## Preparations (7)

- **CrFC26** — C. rotundicauda Factor C cDNA, long form
- **CrFC21** — C. rotundicauda Factor C cDNA, short form
- **TtFC53** — T. tridentatus Factor C cDNA, 5' partial (Muta 1991)
- **TtFC41** — T. tridentatus Factor C cDNA, 3' partial (Muta 1991)
- **CrFC45** — C. rotundicauda clone CrFC45 (non-cross-hybridizing)
- **CrFC63** — C. rotundicauda clone CrFC63 (non-cross-hybridizing)
- **amoebocyteRNA** — C. rotundicauda amoebocyte total/poly(A)+ RNA

## Atomic claims (23)

| ID | basis | stance | conf | claim |
|----|-------|--------|------|-------|
| AC1 | experimental | supports | 0.9 | Factor C cDNA is a rare-copy gene, only 0.03% of the C. rotundicauda amoebocyte library. |
| AC2 | experimental | supports | 0.95 | Two distinct Factor C cDNA forms were cloned: CrFC26 (4182 bp) and CrFC21 (3448 bp). |
| AC3 | experimental | supports | 0.95 | CrFC26 = 568 nt 5'UTR (7 false-start ATGs), 3249-nt ORF, stop, 365 nt 3'UTR. |
| AC4 | experimental | supports | 0.95 | CrFC26 ORF encodes a 24-aa signal peptide + 1059-residue zymogen (1083 aa total). |
| AC5 | computational | supports | 0.85 | Unglycosylated CrFC26 zymogen calc MW 120,244 Da, close to purified native enzyme MW. |
| AC6 | experimental | supports | 0.85 | CrFC contains six potential N-glycosylation sites (Asn-Xaa-Ser/Thr), as in TtFC. |
| AC7 | computational | supports | 0.9 | CrFC has a serine-protease catalytic triad Asp-His-Ser (His873-Asp929-Ser1030 in CrFC26). |
| AC8 | computational | supports | 0.85 | The endotoxin-activation cleavage site is between Phe-Ile (F826-I827 in CrFC26). |
| AC9 | computational | supports | 0.95 | CrFC and TtFC Factor C cDNAs share 97.7% overall sequence homology. |
| AC10 | computational | qualifies | 0.9 | The 3'UTR is the most divergent region (only 86% homology). |
| AC11 | computational | supports | 0.9 | CrFC26 has an extra 716 nt at the 5' end (and 64 extra aa upstream of start Met) vs TtFC53. |
| AC12 | computational | supports | 0.85 | CrFC21 and TtFC53 share identical 5'-end sequence -> CrFC21 is a distinct mRNA, not a truncated CrFC26. |
| AC13 | experimental | supports | 0.9 | Northern (low stringency, TtFC53) shows three bands (15.8, 5.9, 4.0 kNt); high-stringency homologous probe shows only 4.0 kNt. |
| AC14 | experimental | supports | 0.85 | A 368-bp 5'-end probe hybridizes to the ~4 kNt mRNA, confirming the cDNA is full-length. |
| AC15 | experimental | supports | 0.9 | CrFC26 has four polyadenylation signals (AATAAA at nt 183, 239, 2474, 4142; functional one 19 nt upstream of poly(A)). |
| AC16 | experimental | supports | 0.85 | Restriction maps differ by species: CrFC has 2 BamHI sites vs 1 in TtFC53; CrFC26 has 2 HindIII vs 3 in TtFC53. |
| AC17 | computational | supports | 0.8 | Single base substitutions explain inter-species restriction-site differences (BamHI 1549, HindIII 1724/2443, etc.). |
| AC18 | experimental | supports | 0.8 | Two clones (CrFC45, CrFC63) lack an internal EcoRI site and do not cross-hybridize with the 3'/TtFC41 probe. |
| AC19 | computational | supports | 0.8 | CrFC26 5'UTR folds into hairpins obscuring the start codon; CrFC21 presents an exposed AUG. |
| AC20 | computational | supports | 0.85 | Kyte-Doolittle hydropathy of residues 1-59 shows a hydrophobic peak over 1-24, the putative signal peptide. |
| AC21 | computational | supports | 0.8 | CrFC26 has a mosaic architecture: 5 short consensus repeats, 1 lectin domain, 1 EGF-like domain, Cys-rich + Pro-rich regions, serine-protease domain (827-1083); no propeptide/kringle/finger. |
| AC22 | computational | supports | 0.9 | EMBL search: CrFC catalytic domain closest to TtFC (97.7%/777 bp), then thrombins/prothrombins (~52-57%); human hepsin 59.0%/278 bp. |
| AC23 | computational | qualifies | 0.75 | CrFC is structurally closest to prothrombin/thrombin but catalytically trypsin-like, attributed to Asp1024 (analogous to trypsin Asp189). |

<details><summary>quotes & figures</summary>

- **AC1** (Results/Fig 2): "only 0.03% of the cDNA library was positive for Factor C cDNA, indicating its status as a rare copy gene"
- **AC2** (Fig 5/Fig 3): "Two forms of Factor C cDNAs: CrFC21 (3448 bp) and CrFC26 (4182 bp) have been cloned into lambda gt22."
- **AC3** (Fig 5): "568 nucleotides of 5' untranslated sequence containing seven ATGs before the real initiation site, an ORF of 3249 nucleotides ... and 365 nucleotides of 3' untranslated sequence"
- **AC4** (Fig 5): "The ORF codes for a signal peptide of 24 amino acids and a Factor C zymogen of 1059 residues"
- **AC5** (Fig 5/text): "prior to N-glycosylation, has a calculated molecular weight of 120,244 daltons. This is close to the estimated molecular weight of single- and double-chain Factor C enzymes purified from the amoebocytes"
- **AC6** (Fig 5): "similar to TtFC, there are six potential N-glycosylation sites within the CrFC sequence Asn-Xaa-Ser/Thr"
- **AC7** (Fig 5): "also contain the catalytic triad, His809-Asp865-Ser966 for CrFC21 and His873-Asp929-Ser1030 for CrFC26"
- **AC8** (Fig 5): "The unique proteolytic site due to endotoxin-activation of the Factor C enzyme is found between Phe-Ile: F762-I763 for CrFC21, and F826-I827 for CrFC26"
- **AC9** (Fig 5/Table 1): "an overall homology of 97.7%"
- **AC10** (Fig 5): "Most of the dissimilarities ... were found in the 3' UTR, where a lower percentage homology of 86% was observed."
- **AC11** (Fig 5/Fig 7): "the C. rotundicauda cDNA was found to be longer by 716 nucleotides at the 5' end, and it also has an extra 64 amino acids upstream from the starting met"
- **AC12** (Fig 7): "CrFC21 was not merely a truncated species of CrFC26; rather, it was derived from a totally distinct species of mRNA that is exactly identical to the one that gave rise to the T. tridentatus Factor C cDNA"
- **AC13** (Fig 1a,1b): "TtFC probe under low stringency of 42C showed three bands corresponding to 15.8, 5.9, and 4.0 kNt ... hybridization under high stringency with homologous EE fragment of CrFC26 revealed only the 4.0 kNt RNA band"
- **AC14** (Fig 1c): "A single band of approximately 4 kNt ... indicates that the cDNA isolated is full-length and the entire 5' end of CrFC26 unequivocally belongs to this species of Factor C"
- **AC15** (Fig 5): "the canonical hexanucleotide sequence AATAAA is present 19 nucleotides upstream from the polyadenylation site (at nucleotide position 4142). There are three other AATAAA sequences found at nucleotide positions 183, 239, and 2474"
- **AC16** (Fig 3): "CrFC has two BamHI sites compared with only one in TtFC53 ... only has two HindIII sites compared with three in the latter"
- **AC17** (Fig 5/Fig 3): "the absence of the BamHI (GGATCC) site in TtFC ... was due to the substitution of the first G with a T in TtFC ... a C-to-T base substitution ... responsible for the loss of the third HindIII"
- **AC18** (Fig 2/text): "CrFC45 and CrFC63, did not cross-hybridize with either probe ... homologous to only the 5'-end region (EE fragment)"
- **AC19** (Fig 6a,6b): "Numerous hairpin stems and loops are seen for the CrFC26, obscuring its real start codon, whereas CrFC21 showed a well-exposed AUG start site"
- **AC20** (Fig 8): "the first 24 residues to be the putative signal peptide rich in hydrophobic amino acids"
- **AC21** (Fig 5/text): "five short consensus repeats ... one lectin-domain (500-632), one EGF-like domain (167-200) ... The serine protease domain is found at positions 827-1083. No propeptide sequence, kringle domains ... or finger domains were found"
- **AC22** (Table 1): "structurally closest to T. tridentatus Factor C, with 97.7% homology in 777 overlapping nucleotides (Table 1)"
- **AC23** (Table 1/text): "the CrFC is structurally closest to prothrombin and thrombin ... explained by the Asp1024 ... analogous to Asp189 in trypsin ... substrate specificity similar to that of trypsin"

</details>

## Narrative claims (5)

| ID | basis | stance | conf | claim |
|----|-------|--------|------|-------|
| NC1 | computational | supports | 0.8 | High Factor C DNA homology substantiates close molecular-evolutionary proximity of C. rotundicauda and T. tridentatus despite morphological/ecological/taxonomic disparity. |
| NC2 ⚠ | discussion | neutral | 0.6 | The two CrFC cDNA forms arise from differential splicing of the primary transcript around its 5' terminus. |
| NC3 ⚠ | theoretical | neutral | 0.45 | Recombinant C. rotundicauda Factor C is commercially significant as the basis of a rapid endotoxin-detection kit for pharmaceutical QA. |
| NC4 ⚠ | discussion | neutral | 0.4 | CrFC21 constructs express more Factor C than CrFC26 in vitro (absence of false-start ATGs, accessible AUG, Kozak consensus). |
| NC5 ⚠ | theoretical | neutral | 0.4 | C. rotundicauda amoebocyte lysate is reportedly more sensitive to endotoxin than Limulus or Tachypleus lysates (Kim et al. 1988). |

<details><summary>quotes & figures</summary>

- **NC1** (Fig 5/Table 1): "The high degree of homology between Factor C from T. tridentatus and C. rotundicauda substantiates, at the molecular level, the proximity of these two species ... This finding contravenes the apparent disparities with respect to their morphology, ecological habitat, and taxonomical classification."
- **NC2** (): "the existence of the two types of C. rotundicauda Factor C cDNA could be attributable to differential splicing of the initial primary transcript around its 5' terminal"
- **NC3** (): "recombinant Factor C from C. rotundicauda would be of great significance to the pharmaceutical industry, in which pyrogen-detection constitutes an inherent part of quality assurance"
- **NC4** (): "higher expression of Factor C from CrFC21 constructs (our unpublished data, patent pending) ... due to the absence of multiple false-start ATGs ... the more easily accessible AUG, and the presence of a consensus Kozak sequence"
- **NC5** (): "its amoebocyte lysate has been found to be more sensitive to endotoxin than the Limulus or Tachypleus amoebocyte lysates (Kim et al., 1988)"

</details>

## Tally

methods=13 · preparations=7 · atomic=23 · narrative=5