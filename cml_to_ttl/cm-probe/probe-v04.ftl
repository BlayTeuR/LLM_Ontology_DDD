<#attempt>
MAP ${contextMap.name} | type=${(contextMap.type)!"?"} | state=${(contextMap.state)!"?"}
<#list contextMap.relationships as r>
  REL ${(r.name)!"-"} | tech=${(r.implementationTechnology)!"(absent)"}
</#list>
<#recover>(map : ERREUR -- ${.error})</#attempt>
<#attempt>
<#list boundedContexts as bc>
BC ${bc.name} | type=${(bc.type)!"?"} | tech=${(bc.implementationTechnology)!"(absent)"}
<#list bc.aggregates as a>
  AGREGAT ${a.name} | owner=${(a.owner.name)!"(aucun)"}
</#list>
</#list>
<#recover>(bc : ERREUR -- ${.error})</#attempt>