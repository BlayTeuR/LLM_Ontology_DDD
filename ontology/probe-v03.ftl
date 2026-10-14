<#-- ============================================================
  SONDE 0.3.0 (NON TESTEE) : verifie ce que le generateur "generic" expose pour
  les elements ajoutes au metamodele 0.3.0 : attributs, references, textes des BC
  et des agregats, exposedAggregates des relations.
  Elle ne transforme RIEN. Chaque section est isolee (<#attempt>) : si un nom de
  propriete est faux, le message d'erreur s'affiche a sa place et le reste continue.
  Usage (Windows : garder le ./ devant le nom du gabarit) :
    cm generate -i insurance.cml -g generic -t ./probe-v03.ftl -o out -f probe-v03.txt
============================================================ -->
=== 1. TEXTES DES BC ET DES AGREGATS ===
<#attempt>
<#list filterStructuralBoundedContexts(boundedContexts) as bc>
BC ${bc.name}
  domainVisionStatement : ${(bc.domainVisionStatement)!"(absent)"}
  responsibilities      : <#if bc.responsibilities??><#list bc.responsibilities as x>[${x}] </#list><#else>(propriete absente)</#if>
<#list bc.aggregates as a>
  AGREGAT ${a.name} | responsibilities : <#if a.responsibilities??><#list a.responsibilities as x>[${x}] </#list><#else>(propriete absente)</#if>
</#list>
</#list>
<#recover>
(textes : ERREUR -- ${.error})
</#attempt>

=== 2. ATTRIBUTS (String x, Date y...) ===
<#attempt>
<#list filterStructuralBoundedContexts(boundedContexts) as bc>
<#list bc.aggregates as a>
<#list a.domainObjects as o>
<#attempt>
OBJET ${bc.name}/${a.name}/${o.name} | entity=${instanceOf(o, Entity)?c} valueObject=${instanceOf(o, ValueObject)?c} domainEvent=${instanceOf(o, DomainEvent)?c}
<#if o.attributes??>
<#list o.attributes as at>
  attribut : nom=${(at.name)!"?"} | type=${(at.type)!"?"} | collection=${(at.collectionType)!"?"} | brut=${at?string}
</#list>
<#else>
  (propriete "attributes" absente sur cet objet)
</#if>
<#recover>
  (attributs de ${o.name} : ERREUR -- ${.error})
</#attempt>
</#list>
</#list>
</#list>
<#recover>
(attributs : ERREUR -- ${.error})
</#attempt>

=== 3. REFERENCES (- Type nom, - List<Type> nom) ===
<#attempt>
<#list filterStructuralBoundedContexts(boundedContexts) as bc>
<#list bc.aggregates as a>
<#list a.domainObjects as o>
<#attempt>
<#if o.references??>
<#list o.references as r>
REFERENCE ${bc.name}/${a.name}/${o.name} : nom=${(r.name)!"?"} | cible=${(r.domainObjectType.name)!"?"} | collection=${(r.collectionType)!"?"} | brut=${r?string}
</#list>
<#else>
(propriete "references" absente sur ${o.name})
</#if>
<#recover>
(references de ${o.name} : ERREUR -- ${.error})
</#attempt>
</#list>
</#list>
</#list>
<#recover>
(references : ERREUR -- ${.error})
</#attempt>

=== 4. EXPOSED AGGREGATES DES RELATIONS ===
<#attempt>
<#if contextMap??>
<#list contextMap.relationships as r>
<#if instanceOf(r, UpstreamDownstreamRelationship)>
<#attempt>
RELATION ${(r.name)!"(sans nom)"} : ${r.upstream.name} -> ${r.downstream.name} | exposes : <#if r.upstreamExposedAggregates??><#list r.upstreamExposedAggregates as x>${x.name} </#list><#else>(propriete upstreamExposedAggregates absente)</#if>
<#recover>
RELATION ${(r.name)!"(sans nom)"} : ERREUR -- ${.error}
</#attempt>
</#if>
</#list>
</#if>
<#recover>
(exposedAggregates : ERREUR -- ${.error})
</#attempt>
