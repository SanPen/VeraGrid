# Boundary Test Configurations Documentation

Version 4, 24 September 2025

## Introduction
This folder contains the examples of boundary configurations and associated boundary synthetic test data ("Boundary Data") others than the ones associated with the Grid instances of ReliCapGrid. The files included under this folder should be used for pedagogical purposes on how an implementation of the concepts described in ENTSO-E's [Metadata for Dataset and Distribution Specification](https://www.entsoe.eu/data/cim/cim-for-grid-models-exchange/#_Metadata_for_Dataset_and_Distribution_Specification) may look like.

This is a public, anonymised and synthetic test model created by ENTSO-E (formerly European Network of Transmission System Operators for Electricity).

Please, review the .github folder for more information about how to collaborate in the project and its implications.

The Boundary Data is suitable to test the following combinations:

* Modelling of boundary point on a line
* Modelling of boundary point in a substation
* Boundary and common data as separate datasets
* Boundary information per border as separate datasets
* Modelling of boundary points for HVDC link
* Modelling of an IGM and a boundary as datasets without duplication
* Modelling of an IGM that includes the boundary as duplication
* Manifest for a boundary dataset with common data
* Boundary dataset header as in CGMES v3.0 EQBD profile
* Boundary dataset header as in CGMES v3.0 EQ profile
* Boundary dataset header as in NC profiles – extended md:FullModel
* Boundary dataset header as in NC Profiles v2.3.1 – dcat:Dataset based header
* Boundary dataset for HVDC using NC profiles containers

## How to provide feedback
When importing any data contained in the repository, you might find some bugs or issues to report. Please, open a GitHub issue and include your export log.

Do not forget to read [CONTRIBUTING](https://github.com/entsoe-tso/relicapgrid/blob/main/.github/CONTRIBUTING.adoc) file.

## Accreditations
List of the people and organisations contributing to this code.
* AspenTech. 
* Associmates. The test reports were generated using the tool Valimate The Valimate tool creates a field to copyright the generated data. However, ENTSO-E owns the data and thus, such field has been removed.

## Introduction
IEC TS 61970-600-1:2017 and -2: 2017 (CGMES v2.4) has some issues in the
modelling of different configurations of boundary. IEC 61970-600-1 and
-2:2021 (CGMES v3.0) fixes most of the gaps, but still the modelling of
boundary point in a substation is not clear in that version of the
standard. Effort to prepare Conformity Assessment Scheme for CGMES v3.0
highlighted the gaps, but it was too late to address them in the
published version of the standard. Therefore, in May 2023, ENTSO-E
issued the document [Boundary and reference data exchange application
specification](https://www.entsoe.eu/data/cim/cim-for-grid-models-exchange/#_Boundary_and_Reference_Data)
to provide additional specification on boundary point in a substation and
boundary points related to HVDC interconnections.

As there is no test data that represents all possible combinations, and
the official CAS v3.0 data contains some gaps AspenTech defined a set of
test configurations aiming at providing additional details and be able
to provide these configurations to ENTSO-E with a proposal to integrate
them in CGMES CAS.

This document describes the set of prepared boundary test
configurations. There is no confidential data used. All datasets are
either using existing CGMES CAS data or modifications of it.

Screenshots of figures from the document „Boundary and reference data
exchange application specification” are used to illustrate which
modelling option is represented in the test configuration.

Each of the test configurations contain SHACL validation report.
Validation is performed using ValiMate and SHACL based constraints that
are provided by ENTSO-E.

The following variants are prepared and developed in the chapters below:
* Modelling of boundary point on a line
* Modelling of boundary point in a substation
* Boundary and common data as separate datasets
* Boundary information per border as separate datasets
* Modelling of boundary points for HVDC link
* Modelling of an IGM and a boundary as datasets without duplication
* Modelling of an IGM that includes the boundary as duplication
* Manifest for a boundary dataset with common data
* Boundary dataset header as in CGMES v3.0 EQBD profile
* Boundary dataset header as in CGMES v3.0 EQ profile
* Boundary dataset header as in NC profiles – extended md:FullModel
* Boundary dataset header as in NC Profiles v2.3.1 – dcat:Dataset based
header
* Boundary dataset for HVDC using NC profiles containers

## Modelling of boundary point on a line
This is the classical modelling of a boundary point when there is a
ConnectivityNode that splits a tie-line. This concept was used in UCTE
DEF and in supported in CGMES v3.0. The location (electrical middle of
the line, country border, TSO border, elsewhere, etc.) is agreed between
the two connecting parties.

TC datasets:

* [TC-Boundary_point_on_a_line-1IGM](https://github.com/entsoe-tso/relicapgrid/tree/main/Instance/BoundaryConfigurationExamples/TC-Boundary_point_on_a_line-1IGM)
* [TC-Boundary_point_on_a_line-2IGM](https://github.com/entsoe-tso/relicapgrid/tree/main/Instance/BoundaryConfigurationExamples/TC-Boundary_point_on_a_line-2IGM)

Note SV and TP profiles’ datasets are only included for completeness.
They do not contain boundary related information.

Both variants are based on MicroGrid Base Case. In the
TC-Boundary_point_on_a_line-1IGM the TP dataset is edited to include the
necessary references to the boundary in order to satisfy cardinality
constraints.

TC-Boundary_point_on_a_line-1IGM represents the configuration described in Figure 5 of [Boundary and Reference Data Exchange Specification (v1.0)](https://www.entsoe.eu/Documents/CIM_documents/Grid_Model_CIM/Boundary_and_reference_data_exchange_specification_v1.0.pdf). The ConnectivityNode which is the
BoundaryPoint is contained in Line object part of the Boundary dataset.

TC-Boundary_point_on_a_line-2IGM represents the configuration in Figure 11 of [Boundary and Reference Data Exchange Specification (v1.0)](https://www.entsoe.eu/Documents/CIM_documents/Grid_Model_CIM/Boundary_and_reference_data_exchange_specification_v1.0.pdf). The ConnectivityNode which is the
BoundaryPoint is contained in Line object part of the Boundary dataset.

Potential CGMES issues:

* Further instructions shall be given if an IGM shall include all
TopologicalNode objects that are part of the boundary dataset or the
validation instructions shall be considering only BoundaryPoint objects
that are intended to the scope of the validated IGM. Note that this
issue is mitigated when bilateral (per boundaries) are used for the
validation of the IGM.

In case of lack of guidance, the following problems could occur:

* ConnectivityNode.TopologicalNode-cardinality is triggered because the
TP dataset does not include TopologicalNode objects of all BoundaryPoint
objects part of the boundary dataset
* Inclusion of the TopologicalNode objects and the association end
ConnectivityNode.TopologicalNode does not solve the problem as also the
association end Terminal.TopologicalNode is required – note inverse
association is also required. Note: this issue in resolved in CIM18
based profiles by deleting this association from TP profile. In that
case the guidance to use per border boundary works.

A screenshot of CGMES TP profile diagram:

![Extract of CGMES Topology (TP) diagram](https://github.com/entsoe-tso/relicapgrid/blob/main/.github/Media/TCBoundary_TPDiagram.png "Extract of CGMES Topology (TP) diagram")

Validation report notes:

* C:600:EQ:GeographicalRegion:EQ__4 is triggered because the validation
is performed on IGM and boundary datasets together.
* C:301:EQ:ACLineSegment:baseVoltage is a normal warning

## Modelling of boundary point in a substation 

TC dataset: [TC-Boundary-minimal-duplicate](https://github.com/entsoe-tso/relicapgrid/tree/main/Instance/BoundaryConfigurationExamples/TC-Boundary-minimal-duplicate)

TC-Boundary-minimal-duplicate represents the configuration
concept in Figure 12 of [Boundary and Reference Data Exchange Specification (v1.0)](https://www.entsoe.eu/Documents/CIM_documents/Grid_Model_CIM/Boundary_and_reference_data_exchange_specification_v1.0.pdf), where there is minimum duplication of objects.

Validation report notes:

* C:600:EQ:GeographicalRegion:EQ__4 is triggered because the validation
is performed on IGM and boundary datasets together.

The model includes the minimum duplications. A variant where the whole
EQ BD is copied into each of the MAS can be done so that MASes do not
contain dangling references.

The following figure is the diagram of the test configuration. There are
three borders:

* Between Galia and Ampheim (2 boundary points in a substation)
* Between Galia and Belgovia (boundary point on a line)
* Between Galia and Svedala (boundary point on a line)

![Diagram of *TC-Boundary-minimal-duplicate* test configuration](https://github.com/entsoe-tso/relicapgrid/blob/main/.github/Media/TCBoundary_ModellingofBoundaryPointSubstation.png "Diagram of *TC-Boundary-minimal-duplicate* test configuration")

## Boundary and common data as separate datasets

TC dataset: [TC-Boundary_data_split](https://github.com/entsoe-tso/relicapgrid/tree/main/Instance/BoundaryConfigurationExamples/TC-Boundary_data_split)

This test configuration is built on the basis of boundary included in
TC-Boundary-minimal-duplicate. It contains the following two datasets:

* CommonData.xml - which includes common objects
* BoundaryData.xml – which includes ConnectivityNode and BoundaryPoint
objects

## Boundary information per border as separate datasets

TC dataset: [TC-Boundary_split_by_borders](https://github.com/entsoe-tso/relicapgrid/tree/main/Instance/BoundaryConfigurationExamples/TC-Boundary_split_by_borders)

This test configuration is built on the basis of boundary included in
TC-Boundary-minimal-duplicate. The boundary data is further split per
border. It contains the following datasets:

* CommonData.xml - which includes common objects
* BORDER-Galia-Yggrion.xml – which includes objects related to border
Galia-Yggrion
* BORDER-Galia-Belgovia.xml – which includes objects related to border
Galia-Belgovia
* BORDER-Galia-Svedala.xml – which includes objects related to border
Galia-Svedala

## Modelling of boundary points for HVDC link 

This model is built on the ReliCapGrid test configuration used in the SV-IOP
on Network Codes profiles, but additional boundaries and HVDC are added.

The model took many iterations to be able to align and due to the during
the duplication of the boundaries is not complete. It is recommended
that this is looked at when the HVDC containment Line vs new containers
and transition ways are clarified. The model provides the possibility to
model different styles.

TC dataset: [ReliCapGrid](https://github.com/entsoe-tso/relicapgrid/tree/main/Instance/Grid)

The exchanges between in the IGMs in the CGM are as follows


| Name                | Generators P (MW) | Generators Q (MVAr) | Loads P (MW) | Loads P (MVAr) | Losses P (MW) | Losses Q (MVAr) | Interchange Flow P (MW) |
|---------------------|-------------------|---------------------|--------------|----------------|---------------|-----------------|-------------------------|
| Belgovia            | -402.9            | -215.8              | 198.5        | 127.5          | 97.3          | 195.2           | -698.7                  |
| Boundary            | 0.0               | 0.0                 | 0.0          | 0.0            | 0.0           | 0.0             | 41.7                    |
| Britheim            | 160.8             | 28.9                | 20.0         | 0.0            | 40.9          | 60.1            | 99.9                    |
| HVDC-Galia-Nordheim | 0.0               | 0.0                 | 0.0          | 0.0            | 9.8           | 3.2             | -9.8                    |
| HVDC SD-EH          | 0.0               | 0.0                 | 10.0         | 0.0            | 4.0           | -3.6            | -14.0                   |
| Espheim             | 4288.1            | 153.4               | 4332.3       | 1072.5         | 309.6         | 264.9           | -353.9                  |
| Svedala             | 9471.9            | -1091.6             | 8242.5       | 2344.8         | 203.5         | -4510.2         | 1025.9                  |
| Nordheim            | 60.0              | 20.0                | 200.0        | 0.0            | 0.0           | 0.0             | 0.0                     |
| Galia               | 1065.6            | 204.3               | 1125.6       | 552.6          | 31.1          | 67.6            | -91.1                   |

The model contains the following anonymous, synthetic (fake) IGMs:

* Belgovia – developed based on (fake) BE from MicroGrid Test Configuration
* HVDC Espheim-Svedala – an HVDC IGM LCC
* HVDC Nordheim-Galia – an HVDC IGM VSC Bipole
* Britheim – includes HVDC internal interconnection VSC and also some small
grid 1-2 nodes
* Espheim – developed based in SmallGrid Test Configuration
* Svedala – developed based on Svedala test configuration
* Nordheim – only one node
* Galia - developed based on (fake) NL from MicroGrid Test Configuration

Note that the connection between HVDC-Galia-Nordheim and Nordheim area is not
complete in the exported CGM TP/SV results. There is a tooling issue
that needs to be clarified with the duplication principle. However, the
ID of the ConnectivityNode is correct
“_892ef502-162b-469f-b93f-266aae828227”. In the CGM, Nordheim is
separated in a small area

Main issues to be discussed in the SV-IOP:

* Review validation reports as some of the issues may require
modification of SHACL rules, e.g. the validation of dangling references
for header supersedes references
* Discuss HVDC containment Line vs new containers in NC Profiles
* SHACL constraints of the CsConverter
* Ranges for ACDCConverter.udc and cim:DCConductingEquipment.ratedUdc –
closer look is still necessary. It could be a data issue, but there is a
gap in the HVDC model. Polarity was added in CIM18. Decision needs to be
taken for CIM17 validation.

## Modelling of an IGM and a boundary as datasets without duplication

This is the classic situation when for boundary point on a line.
Therefore, this case is covered by Section 2.

This type of modelling is actually only possible when the boundary is on
a line. In case of boundary points in a substation this option is not
possible because it risks cross references between the different MAS
(that are not boundary MAS).

## Modelling of an IGM that includes the boundary as duplication 

Modelling of boundary point on a line is used to illustrate the
duplication.

Here the BoundaryPoints and the containers are part of the IGM.
Basically, the whole boundary is included in the IGM.

TC datasets: [TC-Boundary_point_on_a_line-1IGM_duplication](https://github.com/entsoe-tso/relicapgrid/tree/main/Instance/BoundaryConfigurationExamples/TC-Boundary_point_on_a_line-1IGM_duplication)

Validation report notes (validation performed on IGM without the
boundary set):

* C:600:EQ:GeographicalRegion:EQ__4 is triggered because the boundary is
duplicated.
* C:301:EQ:ACLineSegment:baseVoltage is a normal warning
* C:600:ALL:NA:FBOD4 is the reference to the boundary which is a
dangling reference

Potential CGMES issues:

* The validation process needs to be guided. When there is a duplication
the violation C:600:EQ:GeographicalRegion:EQ__4 will always be
triggered.
* There should be some instructions if md:Model.DependentOn reference
should be present or not in the header.
* There should be guidance if common data should be duplicated or not.

## Manifest for a boundary dataset with common data

TC dataset: [TC-Manifest](https://github.com/entsoe-tso/relicapgrid/tree/main/Instance/BoundaryConfigurationExamples/TC-Manifest)

This test configuration illustrates the Manifest for a zip file that
contains common data and boundary data per border. The common data and
boundary data is the same as the TC-Boundary_split_by_borders.

## Boundary dataset header as in CGMES v3.0 EQBD profile

This is the boundary dataset included in the test configuration
[TC-Boundary-minimal-duplicate](https://github.com/entsoe-tso/relicapgrid/tree/main/Instance/BoundaryConfigurationExamples/TC-Boundary-minimal-duplicate).

## Boundary dataset header as in CGMES v3.0 EQ profile

TC dataset: [TC-Boundary-EQ](https://github.com/entsoe-tso/relicapgrid/tree/main/Instance/BoundaryConfigurationExamples/TC-Boundary-EQ)

The difference is that in the header md:Model.profile is
http://iec.ch/TC57/ns/CIM/CoreEquipment-EU/3.0 and not the equipment
boundary profile.

## Boundary dataset header as in NC profiles – extended md:FullModel

TC dataset: [TC-Boundary-Header-FullModelExtended](https://github.com/entsoe-tso/relicapgrid/tree/main/Instance/BoundaryConfigurationExamples/TC-Boundary-Header-FullModelExtended)

This test configuration uses the extended header, which is applied for
data exchange that conform to NC Profiles v2.2.

## Boundary dataset header as in NC Profiles v2.3.2 – dcat:Dataset based header (v3.0.0)

TC dataset: [TC-Boundary-Header-Dataset](https://github.com/entsoe-tso/relicapgrid/tree/main/Instance/BoundaryConfigurationExamples/TC-Boundary-Header-Dataset)

This test configurations uses the header defined in the NC Profiles
v2.3.2. It is a general illustration, the values of the reference data
may not the exact values to be used in real exchanges as reference data
is being developed.

## Boundary dataset for HVDC using NC profiles containers

It is proposed to use one of the above test configurations and make a
variant of HVDC using new containers. However, this can only be done
after some discussion in the SV-IOP.
