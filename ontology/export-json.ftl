<#-- ============================================================
  EXPORT JSON (brouillon NON TESTE). Aucune logique de mapping : on recopie ce
  que le CML dit. Les noms de roles sont ecrits tels que le generateur les
  affiche (valeurs a lire dans la sortie de probe.ftl) ; c'est le mapper Python
  qui les associera aux classes du metamodele.
  "root": null signifie que la propriete aggregateRoot n'existe pas : le mapper
  Python doit alors s'arreter, pas supposer "faux".
  Usage : cm generate -i insurance.cml -g generic -t export-json.ftl -o out -f insurance.json
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
          "name": <#if r.name?has_content>"${r.name?json_string}"<#else>null</#if>,
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
          "downstream_roles": [<#list r.downstreamRoles as x>"${x?string?json_string}"<#sep>, </#sep></#list>]
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
      "implements": [<#list bc.implementedDomainParts as p>"${p.name?json_string}"<#sep>, </#sep></#list>],
      "aggregates": [
<#list bc.aggregates as a>
        {
          "name": "${a.name?json_string}",
          "objects": [
<#list a.domainObjects as o>
            {
              "name": "${o.name?json_string}",
              "kind": "<#if instanceOf(o, Entity)>entity<#elseif instanceOf(o, ValueObject)>value_object<#elseif instanceOf(o, DomainEvent)>domain_event<#else>other</#if>",
              "root": <#if o.aggregateRoot??>${o.aggregateRoot?c}<#else>null</#if>
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
