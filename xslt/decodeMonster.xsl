<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>

    <xsl:template match="/">
        <html>
            <head>
                <style>
                    body {
                        font-family: "ff-good-web-pro", "Open Sans", sans-serif;
                        line-height: 20px;
                        text-align: justify;
                    }
                    .trait-table { background-color: #d8c384; border-spacing: 2px; }
                    .trait-cell { 
                        color: #FFFFFF; 
                        text-transform: uppercase; 
                        padding: 2px 5px; 
                        text-align: center; 
                        font-weight: bold; 
                        font-size: 0.8em;
                    }
                </style>
            </head>
            <body>
                <xsl:for-each select="monsters/monster">
                    <div style="overflow: hidden;">
                        <h1 style="float: left; text-transform: uppercase; margin: 0;"><xsl:value-of select="name"/></h1>
                        <h1 style="float: right; text-transform: uppercase; margin: 0;">
                            <xsl:value-of select="type"/>&#160;<xsl:value-of select="level"/>
                        </h1>
                    </div>
                    <hr style="clear: both;"/>
               
                    <xsl:apply-templates select="creatureTraits"/>
                    <xsl:apply-templates select="perception"/>
                    <br/>
                    <xsl:apply-templates select="languages"/>
                    <xsl:if test="languages"><br/></xsl:if>
           
                    <xsl:apply-templates select="skills"/>
                    <br/>
                    <xsl:apply-templates select="attributes"/>
                    <br/>
                    <xsl:apply-templates select="interactionAbilities"/>
        
                    <hr/>
                    <xsl:apply-templates select="armorClass"/>
                    <xsl:apply-templates select="saves"/>
                    <br/>
                    <xsl:apply-templates select="health"/>
     
                    <xsl:apply-templates select="weaknesses"/>
                    <xsl:apply-templates select="immunities"/>
                    <xsl:apply-templates select="resistances"/>
                    <br/>
                    <xsl:apply-templates select="reactiveAbilities"/>
 
                    <hr/>
                    <xsl:apply-templates select="speeds"/>
                    <br/>
                    <xsl:apply-templates select="strikes"/>
                    <xsl:apply-templates select="offensiveAbilities"/>
                </xsl:for-each>
            </body>
        </html>
    </xsl:template>

    <xsl:template match="creatureTraits">
        <table class="trait-table">
            <tr>
                <xsl:for-each select="trait">
                    <xsl:variable name="bg">
                        <xsl:choose>
                            <xsl:when test="@type='size'">#497856</xsl:when>
                            <xsl:when test="@type='rarity' and (. = 'RARE' or . = 'UNIQUE')">#14285e</xsl:when>
                            <xsl:otherwise>#560D00</xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <td bgcolor="{$bg}" class="trait-cell">
                        <xsl:value-of select="."/>
                    </td>
                </xsl:for-each>
            </tr>
        </table>
    </xsl:template>

    <xsl:template match="perception">
        <b>Perception&#xA0;</b>
        <xsl:value-of select="bonus"/>
        <xsl:apply-templates select="senses"/>
    </xsl:template>

    <xsl:template match="senses">
        <xsl:text> ; </xsl:text>
        <xsl:for-each select="sens">
            <xsl:value-of select="name"/>
            <xsl:if test="precision">&#xA0;(<xsl:value-of select="precision"/>)</xsl:if>
            <xsl:if test="range">&#xA0;<xsl:value-of select="range"/></xsl:if>
            <xsl:if test="not(position()=last())">, </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="languages">
        <b><xsl:choose>
            <xsl:when test="count(language) = 1">Langue&#xA0;</xsl:when>
            <xsl:otherwise>Langues&#xA0;</xsl:otherwise>
        </xsl:choose></b>
        <xsl:for-each select="language">
            <xsl:value-of select="."/>
            <xsl:if test="not(position()=last())">, </xsl:if>
        </xsl:for-each>
        <xsl:if test="@cannotTalk='TRUE'"> (incapable de parler)</xsl:if>
        <xsl:choose>
            <xsl:when test="specialLang">
                <xsl:text> ; </xsl:text>
                <xsl:value-of select="specialLang"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>.</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="skills">
        <b><xsl:choose>
            <xsl:when test="count(skill) = 1">Compétence </xsl:when>
            <xsl:otherwise>Compétences </xsl:otherwise>
        </xsl:choose></b>
        <xsl:for-each select="skill">
            <xsl:value-of select="name"/>&#xA0;<xsl:value-of select="bonus"/>
            <xsl:if test="skillSpecial"> (<xsl:value-of select="skillSpecial"/>)</xsl:if>
            <xsl:if test="not(position()=last())">, </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="attributes">
        <b>FOR </b><xsl:value-of select="@STR"/>, 
        <b>DEX </b><xsl:value-of select="@DEX"/>, 
        <b>CON </b><xsl:value-of select="@CON"/>, 
        <b>INT </b><xsl:value-of select="@INT"/>, 
        <b>SAG </b><xsl:value-of select="@WIS"/>, 
        <b>CHA </b><xsl:value-of select="@CHA"/>
    </xsl:template>

    <xsl:template match="special">
        <b><xsl:value-of select="name"/></b>
        <xsl:choose>
            <xsl:when test="@type='reaction'">&#xA0;↩</xsl:when>
            <xsl:when test="@type='activity'">
                <xsl:choose>
                    <xsl:when test="@actions=0">&#xA0;◇</xsl:when>
                    <xsl:when test="@actions=1">&#xA0;◆</xsl:when>
                    <xsl:when test="@actions=2">&#xA0;◆◆</xsl:when>
                    <xsl:when test="@actions=3">&#xA0;◆◆◆</xsl:when>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
        <xsl:apply-templates select="traits"/>
        <xsl:if test="not(@type='activity') and not(@type='reaction')">.&#xA0;</xsl:if>
        
        <xsl:if test="frequency"><b> Fréquence </b><xsl:value-of select="frequency"/> ; </xsl:if>
        <xsl:if test="requirements"><b> Conditions </b><xsl:value-of select="requirements"/> ; </xsl:if>
        <xsl:if test="trigger"><b> Déclencheur </b><xsl:value-of select="trigger"/> ; </xsl:if>
        
        <xsl:if test="effect">
            <b>Effet </b><xsl:apply-templates select="effect"/>
        </xsl:if>
        <xsl:if test="description">
            <xsl:apply-templates select="description"/>
        </xsl:if>
        <br/>
    </xsl:template>

    <xsl:template match="interactionAbilities | reactiveAbilities | offensiveAbilities">
        <xsl:apply-templates select="special | spellList"/>
    </xsl:template>

    <xsl:template match="strikes">
        <xsl:apply-templates select="strike"/>
    </xsl:template>

    <xsl:template match="strike">
        <b><xsl:choose>
            <xsl:when test="@type='melee'">Corps à corps </xsl:when>
            <xsl:otherwise>À distance </xsl:otherwise>
        </xsl:choose></b>
        ◆ <xsl:value-of select="name"/>&#xA0;<xsl:value-of select="bonus"/>
        <xsl:apply-templates select="traits"/>, 
        <xsl:apply-templates select="damages"/>
        <xsl:for-each select="extras/extra"> plus <xsl:value-of select="."/></xsl:for-each>
        <br/>
    </xsl:template>

    <xsl:template match="damages">
        <b>Dégâts </b>
        <xsl:for-each select="damage">
            <xsl:if test="position()>1"> plus </xsl:if>
            <xsl:value-of select="amount"/>&#xA0;<xsl:value-of select="damageType"/>
        </xsl:for-each>
    </xsl:template>
    
        <xsl:template match="successDegrees">
        <br/>
        <xsl:if test="criticalSuccess">
            <b>Succès critique. </b><xsl:value-of select="criticalSuccess"/>
            <br/>
        </xsl:if>
        <xsl:if test="success">
            <b>Succès. </b><xsl:value-of select="success"/>
            <br/>
        </xsl:if>
        <xsl:if test="failure">
            <b>Échec. </b><xsl:value-of select="failure"/>
            <br/>
        </xsl:if>
        <xsl:if test="criticalFailure">
            <b>Échec critique. </b><xsl:value-of select="criticalFailure"/>
        </xsl:if>
    </xsl:template>

    <xsl:template match="traits">
        <xsl:text> (</xsl:text>
        <xsl:for-each select="trait">
            <xsl:value-of select="."/>
            <xsl:if test="not(position()=last())">, </xsl:if>
        </xsl:for-each>
        <xsl:text>)</xsl:text>
    </xsl:template>

    <xsl:template match="spellList">
        <b>Sorts <xsl:if test="@source='innate'">innés </xsl:if>
        <xsl:if test="@tradition='primal'">primordiaux </xsl:if></b>
        DD <xsl:value-of select="@DD"/> ; 
        <xsl:for-each select="rank">
            <b>
                <xsl:choose>
                    <xsl:when test="@constant='TRUE'">Constant (<xsl:value-of select="@rank"/>e)</xsl:when>
                    <xsl:when test="@cantrips='TRUE'">Tours de magie (<xsl:value-of select="@rank"/>e)</xsl:when>
                    <xsl:otherwise><xsl:value-of select="@rank"/>e</xsl:otherwise>
                </xsl:choose>
            </b>
            <xsl:for-each select="spells/spell">
                &#xA0;<xsl:apply-templates select="."/>
                <xsl:if test="not(position()=last())">, </xsl:if>
            </xsl:for-each>
            <xsl:if test="not(position()=last())"> ; </xsl:if>
        </xsl:for-each>
        <br/>
    </xsl:template>

    <xsl:template match="spell">
        <i><xsl:value-of select="."/></i>
        <xsl:if test="@source"> (<xsl:value-of select="@source"/>)</xsl:if>
        <xsl:if test="@spellSpecial"> (<xsl:value-of select="@spellSpecial"/>)</xsl:if>
    </xsl:template>

    <xsl:template match="list">
        <ul>
            <xsl:for-each select="listItem">
                <li><xsl:apply-templates select="."/></li>
            </xsl:for-each>
        </ul>
    </xsl:template>
    
    <xsl:template match="table">
        <table style="border-collapse: collapse;
                      box-sizing: border-box;
                      color: rgb(34, 34, 34);
                      margin-top: 0px;
                      text-align: left;">
            <xsl:if test="headerLine">
                <tr style="background: #5D0000 !important;
                           color: #fff !important;">
                    <xsl:for-each select="headerLine/cell">
                        <th><xsl:value-of select="."/></th>
                    </xsl:for-each>
                </tr>
            </xsl:if>
            <xsl:for-each select="line">
                <xsl:choose>
                    <xsl:when test="position() mod 2 =0">
                        <tr style="background: #EDE3C7 !important">
                            <xsl:for-each select="cell">
                                <td><xsl:value-of select="."/></td>
                            </xsl:for-each>
                        </tr>
                    </xsl:when>
                    <xsl:otherwise>
                        <tr style="background: #F4EEE0 !important">
                            <xsl:for-each select="cell">
                                <td><xsl:value-of select="."/></td>
                            </xsl:for-each>
                        </tr>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>
        </table>
    </xsl:template>

    <xsl:template match="armorClass"><b>CA </b><xsl:value-of select="."/> ; </xsl:template>
    <xsl:template match="health"><b>PV </b><xsl:value-of select="."/></xsl:template>
    <xsl:template match="saves">
        <b> Réf </b><xsl:value-of select="@REF"/>, <b> Vig </b><xsl:value-of select="@FOR"/>, <b> Vol </b><xsl:value-of select="@VOL"/>
        <xsl:if test="@saveSpecial"> ; <xsl:value-of select="@saveSpecial"/></xsl:if>
    </xsl:template>
</xsl:stylesheet>