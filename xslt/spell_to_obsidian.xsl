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
</xsl:stylesheet>