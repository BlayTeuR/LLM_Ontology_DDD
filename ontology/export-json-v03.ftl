<#-- ============================================================
  EXPORT JSON 0.3.0 (NON TESTE). Aucune logique de mapping : on recopie ce que
  le CML dit. Les noms de proprietes ajoutes par rapport a export-json.ftl ont
  ete CONFIRMES par la sonde probe-v03.ftl sur insurance.cml :
    bc.domainVisionStatement, bc.responsibilities, a.responsibilities,
    o.attributes (name, type, collectionType), o.references (name,
    domainObjectType.name, collectionType), r.upstreamExposedAggregates.
  Seul l'acces au proprietaire de la cible d'une reference
  (domainObjectType.eContainer()) n'est PAS confirme : il est entoure d'un
  <#attempt> et vaut null s'il echoue ; le mapper resout alors la cible par son nom.
  "root": null signifie que la propriete aggregateRoot n'existe pas : le mapper
  Python doit alors s'arreter, pas supposer "faux".
  Usage (Windows : garder le ./) :
    cm generate -i insurance.cml -g generic -t ./export-json-v03.ftl -o out -f insurance-v03.json
============================================================ -->
{
  "file": "${fileName?json_string}",
  "imports": [<#list imports as i>"${i.importURI?json_string}"<#sep>, </#sep></#list>],
  "context_maps": [
<#if contextMap??>
    {
      "name": "${contextMap.name?json_string}",
      "contexts": [<#list filterStructuralBoundedContexts(contextMap.boundedContexts) as bc>"${bc.name?json_string}"<#sep>, </#sep></#list>],
      "relationships": [
<#list contextMap.relationships as r>
        {
          "name": <#if (r.name)?has_content>"${r.name?json_string}"<#else>null</#if>,
<#if instanceOf(r, SymmetricRelationship)>
          "kind": "symmetric",
          "subtype": "<#if instanceOf(r, Partnership)>Partnership<#else>SharedKernel</#if>",
          "participants": ["${r.participant1.name?json_string}", "${r.participant2.name?json_string}"]
<#else>
          "kind": "upstream_downstream",
          "customer_supplier": ${instanceOf(r, CustomerSupplierRelationship)?c},
          "upstream": "${r.upstream.name?json_string}",
          "downstream": "${r.downstream.name?json_string}",
          "upstream_roles": [<#list r.upstreamRoles as x>"${x?string?json_string}"<#sep>, </#sep></#list>],
          "downstream_roles": [<#list r.downstreamRoles as x>"${x?string?json_string}"<#sep>, </#sep></#list>],
          "exposes_aggregates": [<#if r.upstreamExposedAggregates??><#list r.upstreamExposedAggregates as x>"${x.name?json_string}"<#sep>, </#sep></#list></#if>]
</#if>
        }<#sep>,</#sep>
</#list>
      ]
    }
</#if>
  ],
  "bounded_contexts": [
<#list filterStructuralBoundedContexts(boundedContexts) as bc>
    {
      "name": "${bc.name?json_string}",
      "domain_vision_statement": <#if (bc.domainVisionStatement)?has_content>"${bc.domainVisionStatement?json_string}"<#else>null</#if>,
      "responsibilities": [<#if bc.responsibilities??><#list bc.responsibilities as x>"${x?json_string}"<#sep>, </#sep></#list></#if>],
      "implements": [<#list bc.implementedDomainParts as p>"${p.name?json_string}"<#sep>, </#sep></#list>],
      "aggregates": [
<#list bc.aggregates as a>
        {
          "name": "${a.name?json_string}",
          "responsibilities": [<#if a.responsibilities??><#list a.responsibilities as x>"${x?json_string}"<#sep>, </#sep></#list></#if>],
          "objects": [
<#list a.domainObjects as o>
            {
              "name": "${o.name?json_string}",
              "kind": "<#if instanceOf(o, Entity)>entity<#elseif instanceOf(o, ValueObject)>value_object<#elseif instanceOf(o, DomainEvent)>domain_event<#else>other</#if>",
              "root": <#if o.aggregateRoot??>${o.aggregateRoot?c}<#else>null</#if>,
              "attributes": [<#if o.attributes??><#list o.attributes as at>{ "name": "${at.name?json_string}", "type": "${((at.type)!"")?json_string}", "collection": "${(at.collectionType)!"None"}" }<#sep>, </#sep></#list></#if>],
              "references": [<#if o.references??><#list o.references as rf>{ "name": "${rf.name?json_string}", "target": "${rf.domainObjectType.name?json_string}", "collection": "${(rf.collectionType)!"None"}", "target_aggregate": <#attempt>"${rf.domainObjectType.eContainer().name?json_string}"<#recover>null</#attempt>, "target_bc": <#attempt>"${rf.domainObjectType.eContainer().eContainer().name?json_string}"<#recover>null</#attempt> }<#sep>, </#sep></#list></#if>]
            }<#sep>,</#sep>
</#list>
          ]
        }<#sep>,</#sep>
</#list>
      ]
    }<#sep>,</#sep>
</#list>
  ],
  "domains": [
<#list domains as d>
<#if instanceOf(d, Domain)>
    {
      "name": "${d.name?json_string}",
      "subdomains": [
<#list d.subdomains as s>
        { "name": "${s.name?json_string}", "type": "${(s.type)!""}" }<#sep>,</#sep>
</#list>
      ]
    }<#sep>,</#sep>
</#if>
</#list>
  ]
}
