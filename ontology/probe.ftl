<#-- ============================================================
  SONDE (non testee) : affiche ce que le generateur "generic" de Context Mapper
  expose pour un fichier CML. Elle ne transforme RIEN : elle sert a decider
  du parser (phase 1). Chaque section est isolee : si l'une echoue, le message
  d'erreur s'affiche et les autres continuent.
  Usage : cm generate -i insurance.cml -g generic -t probe.ftl -o out -f probe.txt
============================================================ -->
VERSION: ${contextMapperVersion!"?"} | FICHIER: ${fileName!"?"}

=== IMPORTS ===
<#attempt>
<#list imports as i>
import: ${i.importURI!"?"}
</#list>
<#recover>
(imports : ERREUR -- ${.error})
</#attempt>

=== CARTE ET RELATIONS ===
<#attempt>
<#if contextMap??>
carte: ${contextMap.name} | type=${(contextMap.type)!"?"} | state=${(contextMap.state)!"?"}
<#list contextMap.boundedContexts as bc>
  contient: ${bc.name}
</#list>
<#list contextMap.relationships as r>
RELATION nom=${(r.name)!"(sans nom)"}
<#attempt>
<#if instanceOf(r, SymmetricRelationship)>
  SYMETRIQUE : ${r.participant1.name} <-> ${r.participant2.name}
</#if>
<#if instanceOf(r, UpstreamDownstreamRelationship)>
  AMONT-AVAL : amont=${r.upstream.name} aval=${r.downstream.name}
  customer-supplier : ${instanceOf(r, CustomerSupplierRelationship)?c}
  roles amont : <#list r.upstreamRoles as x>${x} </#list>
  roles aval  : <#list r.downstreamRoles as x>${x} </#list>
</#if>
<#recover>
  (relation : ERREUR -- ${.error})
</#attempt>
</#list>
<#else>
(pas de carte)
</#if>
<#recover>
(carte : ERREUR -- ${.error})
</#attempt>

=== CONTEXTES (hors equipes), AGREGATS ET OBJETS ===
<#attempt>
<#list filterStructuralBoundedContexts(boundedContexts) as bc>
BC ${bc.name} | type=${(bc.type)!"?"}
  implements : <#list bc.implementedDomainParts as p>${p.name} </#list>
<#list bc.aggregates as a>
  AGREGAT ${a.name}
<#list a.domainObjects as o>
    OBJET ${o.name} | entity=${instanceOf(o, Entity)?c} valueObject=${instanceOf(o, ValueObject)?c} domainEvent=${instanceOf(o, DomainEvent)?c} | racine=<#if o.aggregateRoot??><#if o.aggregateRoot>oui<#else>non</#if><#else>PROPRIETE ABSENTE</#if>
</#list>
</#list>
</#list>
<#recover>
(contextes : ERREUR -- ${.error})
</#attempt>

=== EQUIPES (type TEAM) ===
<#attempt>
<#list filterTeams(boundedContexts) as t>
equipe: ${t.name}
</#list>
<#recover>
(equipes : ERREUR -- ${.error})
</#attempt>

=== DOMAINES ET SOUS-DOMAINES ===
<#attempt>
<#list domains as d>
${d.name} | type=${(d.type)!"-"} | domaine=${instanceOf(d, Domain)?c}
<#if d.subdomains??>
<#list d.subdomains as s>
  sous-domaine ${s.name} | type=${(s.type)!"?"} | entities=<#if s.entities??>${s.entities?size}<#else>absent</#if>
</#list>
</#if>
</#list>
<#recover>
(domaines : ERREUR -- ${.error})
</#attempt>

=== NUMEROS DE LIGNE ===
(le generateur n'est pas documente comme les exposant : cherche ici s'il y en a)
