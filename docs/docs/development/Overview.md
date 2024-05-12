# Overview

This article provides an overview of the ACME CSE's architecture, components, and database schemas. 

## Components

The ACME CSE is divided into several components. The following diagram shows the components and their relationships.

<figure markdown="1">
![UML Component Diagram of the ACME CSE](../images/cse_uml.png#only-light){data-gallery="light"}
![UML Component Diagram of the ACME CSE](../images/cse_uml-dark.png#only-dark){data-gallery="dark"}
<figcaption>UML Component Diagram of the ACME CSE</figcaption>
</figure>

## Resource Class Hierarchy

The CSE's resources are implemented as classes. The following diagram shows the class hierarchy of the resources.

<figure markdown="1">
![UML Class Diagram of the ACME CSE Resources](../images/resources_uml.png#only-light){data-gallery="light"}
![UML Class Diagram of the ACME CSE Resources](../images/resources_uml-dark.png#only-dark){data-gallery="dark"}
<figcaption>UML Class Diagram of the ACME CSE Resources</figcaption>
</figcaption>
</figure>

## Database Schemas

<figure markdown="1">
![Database Schemas of the ACME CSE](../images/db_schemas.png#only-light){data-gallery="light"}
![Database Schemas of the ACME CSE](../images/db_schemas-dark.png#only-dark){data-gallery="dark"}
<figcaption>Database Schemas of the ACME CSE</figcaption>
</figcaption>
</figure>

If the *tinyDB* database mode is used the database files are stored in the `data` sub-directory of the CSE's working directory. 

The database used by the CSE is [TinyDB](https://github.com/msiemens/tinydb){target=_new} which uses plain JSON files for storing the data. Some files only contain a single data table while other contain multiple tables.

The filenames include the *CSE-ID* of the running CSE, so if multiple CSEs are running and are using the same data directory then they won't interfere with each other. The database files are copied to a *backup* directory at CSE startup.

Some database tables duplicate attributes from actual resources, e.g. in the *subscription* database. This is mainly done for optimization reasons in order to prevent a retrieval and instantiation of a full resource when only a few attributes are needed.
