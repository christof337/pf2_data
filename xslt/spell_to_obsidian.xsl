<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text" encoding="UTF-8"/>

  <!-- Template réutilisable : convertit un chiffre d'action en libellé pf2e-stats -->
  <xsl:template name="action-label">
    <xsl:param name="n"/>
    <xsl:choose>
      <xsl:when test="$n='1'">one-action</xsl:when>
      <xsl:when test="$n='2'">two-actions</xsl:when>
      <xsl:when test="$n='3'">three-actions</xsl:when>
      <xsl:when test="$n='R' or $n='reaction'">reaction</xsl:when>
      <xsl:when test="$n='free'">free-action</xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="/spells/spell">
    <xsl:text>&#10;&#10;</xsl:text>

    <xsl:text>&#96;&#96;&#96;pf2e-stats&#10;</xsl:text>
    <xsl:text>#### [[fr]]&#10;</xsl:text>

    <xsl:text># </xsl:text><xsl:value-of select="name"/>
    <xsl:if test="actions">
      <xsl:choose>
        <!-- Actions variables : "1-3" → `[one-action]` à `[three-actions]` -->
        <xsl:when test="contains(actions, '-')">
          <xsl:text> &#96;[</xsl:text>
          <xsl:call-template name="action-label">
            <xsl:with-param name="n" select="substring-before(actions, '-')"/>
          </xsl:call-template>
          <xsl:text>]&#96; à &#96;[</xsl:text>
          <xsl:call-template name="action-label">
            <xsl:with-param name="n" select="substring-after(actions, '-')"/>
          </xsl:call-template>
          <xsl:text>]&#96;</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text> &#96;[</xsl:text>
          <xsl:call-template name="action-label">
            <xsl:with-param name="n" select="actions"/>
          </xsl:call-template>
          <xsl:text>]&#96;</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
    <xsl:text>&#10;</xsl:text>
    
    <xsl:text>## </xsl:text>
    <xsl:choose>
      <xsl:when test="@type='cantrip'">TOUR DE MAGIE </xsl:when>
      <xsl:when test="@type='focus'">FOCALISÉ </xsl:when>
      <xsl:when test="@type='spell'">SORT </xsl:when>
    </xsl:choose><xsl:value-of select="rank"/><xsl:text>&#10;</xsl:text>
    <xsl:text>----&#10;</xsl:text>
    
    <xsl:for-each select="traits/trait">
      <xsl:sort select="number(not(@type = 'rarity'))" order="ascending" data-type="number"/>
      <xsl:sort select="." order="ascending"/>
      <xsl:text>==</xsl:text><xsl:value-of select="."/><xsl:text>==</xsl:text>
      <xsl:if test="position() != last()"><xsl:text> </xsl:text></xsl:if>
    </xsl:for-each>
    <xsl:text>&#10;</xsl:text>
    
    <xsl:text>**Traditions** </xsl:text>
    <xsl:for-each select="traditions/tradition">
      <xsl:value-of select="."/>
      <xsl:if test="position() != last()">, </xsl:if>
    </xsl:for-each>
    <xsl:text>&#10;</xsl:text>
    
    <xsl:if test="cast">
      <xsl:text>**Incantation** </xsl:text><xsl:value-of select="cast"/>
      <xsl:text>&#10;</xsl:text>
    </xsl:if>
    <xsl:if test="cost">
      <xsl:text>**Coût** </xsl:text><xsl:value-of select="cost"/>
      <xsl:text>&#10;</xsl:text>
    </xsl:if>
    <xsl:if test="condition">
      <xsl:text>**Conditions** </xsl:text><xsl:value-of select="condition"/>
      <xsl:text>&#10;</xsl:text>
    </xsl:if>
    <xsl:if test="trigger">
      <xsl:text>**Déclencheur** </xsl:text><xsl:value-of select="trigger"/>
      <xsl:text>&#10;</xsl:text>
    </xsl:if>
    
    <xsl:if test="range">
      <xsl:text>**Portée** </xsl:text>
      <xsl:value-of select="range"/>
      <xsl:if test="targets || area">
        <xsl:text> ; </xsl:text>
      </xsl:if>
    </xsl:if>
    <xsl:if test="area">
      <xsl:text>**Zone** </xsl:text>
      <xsl:value-of select="area"/>
      <xsl:if test="targets">
        <xsl:text> ; </xsl:text>">
      </xsl:if>
    </xsl:if>
    <xsl:if test="targets">
      <xsl:text>**Cible** </xsl:text><xsl:value-of select="targets"/>
    </xsl:if>
    
    <xsl:text>&#10;</xsl:text>

    <xsl:if test="defense">
      <xsl:text>**Défense** </xsl:text><xsl:value-of select="defense"/>
      <xsl:if test="duration">
        <xsl:text> ; </xsl:text>
      </xsl:if>
    </xsl:if>
    <xsl:if test="duration">
      <xsl:text>**Durée** </xsl:text><xsl:value-of select="duration"/>
    </xsl:if>
    
    <xsl:text>&#10;---- &#10;</xsl:text>
    
    <xsl:apply-templates select="description"/>
    <!-- <xsl:value-of select="description"/> -->
    <xsl:text> &#10;</xsl:text>
    
    <xsl:if test="savingThrow/criticalSuccess">
      <xsl:text>**Succès critique.** </xsl:text><xsl:apply-templates select="savingThrow/criticalSuccess"/><xsl:text>  &#10;</xsl:text>
    </xsl:if>
    <xsl:if test="savingThrow/success">
      <xsl:text>**Succès.** </xsl:text><xsl:apply-templates select="savingThrow/success"/><xsl:text>  &#10;</xsl:text>
    </xsl:if>
    <xsl:if test="savingThrow/failure">
      <xsl:text>**Échec.** </xsl:text><xsl:apply-templates select="savingThrow/failure"/><xsl:text>&#10;</xsl:text>
    </xsl:if>
    <xsl:if test="savingThrow/criticalFailure">
      <xsl:text>**Échec critique.** </xsl:text><xsl:apply-templates select="savingThrow/criticalFailure"/><xsl:text>&#10;</xsl:text>
    </xsl:if>
    
    <xsl:if test="heightenList">
      <xsl:text>&#10;----</xsl:text>
      <xsl:for-each select="heightenList/heighten">
        <xsl:text>&#10;**Intensifié (</xsl:text><xsl:value-of select="@type"/><xsl:text>).** </xsl:text><xsl:value-of select="."/><xsl:text>&#10;</xsl:text>
      </xsl:for-each>
    </xsl:if>

    <xsl:apply-templates select="table"/>
  </xsl:template>

  <xsl:template match="table">
    <xsl:text>&#10;</xsl:text>
    <xsl:if test="headerLine">
      <xsl:text>| </xsl:text>
      <xsl:for-each select="headerLine/cell">
        <xsl:value-of select="."/><xsl:text> | </xsl:text>
      </xsl:for-each>
      <xsl:text>&#10;|</xsl:text>
      <xsl:for-each select="headerLine/cell"><xsl:text>---|</xsl:text></xsl:for-each>
      <xsl:text>&#10;</xsl:text>
    </xsl:if>
    <xsl:for-each select="line">
      <xsl:text>| </xsl:text>
      <xsl:for-each select="cell">
        <xsl:value-of select="."/><xsl:text> | </xsl:text>
      </xsl:for-each>
      <xsl:text>&#10;</xsl:text>
    </xsl:for-each>
  </xsl:template>
  
  <xsl:template match="spellRef">
    <xsl:text>*</xsl:text><xsl:value-of select="."/><xsl:text>*</xsl:text>
  </xsl:template>

  <xsl:template match="list">
    <xsl:text>&#10;</xsl:text>
    <xsl:for-each select="listItem">
      <xsl:text>- </xsl:text><xsl:value-of select="."/><xsl:text>&#10;</xsl:text>
    </xsl:for-each>
  </xsl:template>

  <xsl:template match="battleForm">
    <xsl:text>&#10;</xsl:text>
    <!-- Statistiques globales -->
    <xsl:if test="globalStats">
      <xsl:text>&#10;| CA | PV temp. | Mod. attaque | Mod. dégâts | </xsl:text>
      <xsl:choose>
        <xsl:when test="globalStats/skillName"><xsl:value-of select="globalStats/skillName"/></xsl:when>
        <xsl:otherwise>Athlétisme</xsl:otherwise>
      </xsl:choose>
      <xsl:text> | Sens |&#10;</xsl:text>
      <xsl:text>|---|---|---|---|---|---|&#10;</xsl:text>
      <xsl:text>| </xsl:text>
      <xsl:choose>
        <xsl:when test="globalStats/ac"><xsl:value-of select="globalStats/ac"/></xsl:when>
        <xsl:otherwise>—</xsl:otherwise>
      </xsl:choose>
      <xsl:text> | </xsl:text>
      <xsl:choose>
        <xsl:when test="globalStats/tempHp"><xsl:value-of select="globalStats/tempHp"/></xsl:when>
        <xsl:otherwise>—</xsl:otherwise>
      </xsl:choose>
      <xsl:text> | </xsl:text>
      <xsl:choose>
        <xsl:when test="globalStats/attackBonus"><xsl:value-of select="globalStats/attackBonus"/></xsl:when>
        <xsl:otherwise>—</xsl:otherwise>
      </xsl:choose>
      <xsl:text> | </xsl:text>
      <xsl:choose>
        <xsl:when test="globalStats/damageBonus"><xsl:value-of select="globalStats/damageBonus"/></xsl:when>
        <xsl:otherwise>—</xsl:otherwise>
      </xsl:choose>
      <xsl:text> | </xsl:text>
      <xsl:choose>
        <xsl:when test="globalStats/athletics"><xsl:value-of select="globalStats/athletics"/></xsl:when>
        <xsl:otherwise>—</xsl:otherwise>
      </xsl:choose>
      <xsl:text> | </xsl:text>
      <xsl:choose>
        <xsl:when test="globalStats/senses"><xsl:value-of select="globalStats/senses"/></xsl:when>
        <xsl:otherwise>—</xsl:otherwise>
      </xsl:choose>
      <xsl:text> |&#10;</xsl:text>
      <!-- Vitesse globale (ex: FORME DE DRAGON) -->
      <xsl:if test="globalStats/speed">
        <xsl:text>**Vitesse** </xsl:text><xsl:value-of select="globalStats/speed"/><xsl:text>&#10;</xsl:text>
      </xsl:if>
      <!-- Notes globales (Faiblesse, Résistance, Souffle, etc.) -->
      <xsl:for-each select="globalStats/note">
        <xsl:text>- </xsl:text><xsl:value-of select="."/><xsl:text>&#10;</xsl:text>
      </xsl:for-each>
      <!-- Frappes globales (ex: FORME DE DRAGON) -->
      <xsl:if test="globalStats/strike">
        <xsl:text>&#10;| Frappe | Traits | Dégâts |&#10;</xsl:text>
        <xsl:text>|---|---|---|&#10;</xsl:text>
        <xsl:for-each select="globalStats/strike">
          <xsl:text>| </xsl:text>
          <xsl:choose>
            <xsl:when test="@type='melee'">**Corps à corps** </xsl:when>
            <xsl:when test="@type='ranged'">**À distance** </xsl:when>
          </xsl:choose>
          <xsl:value-of select="name"/>
          <xsl:text> | </xsl:text>
          <xsl:for-each select="traits/trait">
            <xsl:value-of select="."/>
            <xsl:if test="position() != last()">, </xsl:if>
          </xsl:for-each>
          <xsl:text> | </xsl:text>
          <xsl:for-each select="damages/damage">
            <xsl:if test="amount != ''">
              <xsl:value-of select="amount"/><xsl:text> </xsl:text>
            </xsl:if>
            <xsl:value-of select="damageType"/>
            <xsl:if test="position() != last()"> plus </xsl:if>
          </xsl:for-each>
          <xsl:text> |&#10;</xsl:text>
        </xsl:for-each>
      </xsl:if>
      <xsl:text>&#10;</xsl:text>
    </xsl:if>
    <!-- Tableau des formes (conditionnel) -->
    <xsl:if test="formEntry">
      <xsl:text>| Forme | Vitesse | Frappe | Traits | Dégâts |</xsl:text>
      <xsl:if test="formEntry/note"><xsl:text> Note |</xsl:text></xsl:if>
      <xsl:text>&#10;|---|---|---|---|---|</xsl:text>
      <xsl:if test="formEntry/note"><xsl:text>---|</xsl:text></xsl:if>
      <xsl:text>&#10;</xsl:text>
      <xsl:for-each select="formEntry">
        <!-- Forme sans frappe : une ligne avec — dans les colonnes de frappe -->
        <xsl:if test="not(strike)">
          <xsl:text>| **</xsl:text><xsl:value-of select="name"/><xsl:text>** | </xsl:text>
          <xsl:value-of select="speed"/>
          <xsl:text> | — | — | — |</xsl:text>
          <xsl:if test="../formEntry/note">
            <xsl:text> </xsl:text>
            <xsl:for-each select="note">
              <xsl:value-of select="."/>
              <xsl:if test="position() != last()">; </xsl:if>
            </xsl:for-each>
            <xsl:text> |</xsl:text>
          </xsl:if>
          <xsl:text>&#10;</xsl:text>
        </xsl:if>
        <xsl:for-each select="strike">
          <xsl:text>| </xsl:text>
          <xsl:if test="position() = 1">**<xsl:value-of select="../name"/>**</xsl:if>
          <xsl:text> | </xsl:text>
          <xsl:if test="position() = 1"><xsl:value-of select="../speed"/></xsl:if>
          <xsl:text> | </xsl:text>
          <xsl:choose>
            <xsl:when test="@type='melee'">**Corps à corps** </xsl:when>
            <xsl:when test="@type='ranged'">**À distance** </xsl:when>
          </xsl:choose>
          <xsl:value-of select="name"/>
          <xsl:text> | </xsl:text>
          <xsl:for-each select="traits/trait">
            <xsl:value-of select="."/>
            <xsl:if test="position() != last()">, </xsl:if>
          </xsl:for-each>
          <xsl:text> | </xsl:text>
          <xsl:for-each select="damages/damage">
            <xsl:if test="amount != ''">
              <xsl:value-of select="amount"/>
              <xsl:text> </xsl:text>
            </xsl:if>
            <xsl:value-of select="damageType"/>
            <xsl:if test="position() != last()"> plus </xsl:if>
          </xsl:for-each>
          <xsl:text> |</xsl:text>
          <!-- Colonne Note : toujours présente si le tableau a une colonne Note -->
          <xsl:if test="ancestor::battleForm/formEntry/note">
            <xsl:text> </xsl:text>
            <xsl:if test="position() = 1">
              <xsl:for-each select="../note">
                <xsl:value-of select="."/>
                <xsl:if test="position() != last()">; </xsl:if>
              </xsl:for-each>
            </xsl:if>
            <xsl:text> |</xsl:text>
          </xsl:if>
          <xsl:text>&#10;</xsl:text>
        </xsl:for-each>
      </xsl:for-each>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>